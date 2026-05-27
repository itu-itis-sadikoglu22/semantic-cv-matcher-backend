from fastapi import APIRouter, HTTPException, Query

from app.api.routes.cv import cv_storage
from app.api.routes.job import job_storage
from app.schemas.match import (
    MatchRequest,
    CVTopKMatchResponse,
    MatchResponse,
    MatchResult,
    TopKMatchResponse,
)
from app.services.embedding import generate_embedding
from app.services.ner import extract_entities
from app.services.ranking import (
    calculate_experience_score,
    calculate_final_score,
    calculate_skill_match_score,
)
from app.services.similarity import (
    calculate_cosine_similarity,
    calculate_percentage_score,
)

from app.services.location import normalize_location

router = APIRouter()


def _build_match_result(
    cv_text: str,
    job_text: str,
    candidate_years_experience: float | None = None,
    required_years_experience: float | None = None,
) -> MatchResult:
    """
    Build a semantic and explainable match result for one CV-job pair.
    """

    cv_embedding = generate_embedding(cv_text)
    job_embedding = generate_embedding(job_text)

    similarity_score = calculate_cosine_similarity(cv_embedding, job_embedding)
    semantic_score = calculate_percentage_score(similarity_score)

    cv_entities = extract_entities(cv_text)
    job_entities = extract_entities(job_text)

    matched_skills = sorted(
        set(cv_entities.skills).intersection(set(job_entities.skills))
    )

    skill_score = calculate_skill_match_score(
        cv_skills=cv_entities.skills,
        job_skills=job_entities.skills,
    )

    experience_score = calculate_experience_score(
        candidate_years=candidate_years_experience,
        required_years=required_years_experience,
    )

    final_score = calculate_final_score(
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
    )

    explanation = (
        f"The CV and job posting have a semantic score of {semantic_score}%. "
        f"The skill match score is {skill_score}%, and the experience score is "
        f"{experience_score}%. The final weighted ranking score is {final_score}%. "
        f"Matched skills: {', '.join(matched_skills) if matched_skills else 'none'}."
    )

    return MatchResult(
        similarity_score=round(similarity_score, 4),
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
        final_score=final_score,
        matched_skills=matched_skills,
        explanation=explanation,
        cv_entities=cv_entities,
        job_entities=job_entities,
    )


@router.post("/match/text", response_model=MatchResponse)
async def match_cv_and_job_text(request: MatchRequest):
    """
    Match a CV text and a job posting text using semantic similarity and ranking signals.
    """

    result = _build_match_result(
        cv_text=request.cv_text,
        job_text=request.job_text,
        candidate_years_experience=request.candidate_years_experience,
        required_years_experience=request.required_years_experience,
    )

    return MatchResponse(result=result)


@router.post("/match/job/{job_id}", response_model=TopKMatchResponse)
async def match_job_with_stored_cvs(
    job_id: int,
    top_k: int = Query(default=5, ge=1, le=20),
    location: str | None = None,
    min_final_score: float | None = Query(default=None, ge=0, le=100),
):
    """
    Match a stored job posting with all temporarily stored CVs and return top-k results.
    """

    selected_job = next(
        (job for job in job_storage if job["id"] == job_id),
        None,
    )

    if selected_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job posting not found.",
        )

    if not cv_storage:
        raise HTTPException(
            status_code=404,
            detail="No CV records found. Please ingest at least one CV first.",
        )

    ranked_results = []

    for cv in cv_storage:
        if location:
            normalized_filter_location = normalize_location(location)
            normalized_cv_location = normalize_location(cv.get("location"))

        if normalized_cv_location != normalized_filter_location:
            continue

        match_result = _build_match_result(
            cv_text=cv["raw_text"],
            job_text=selected_job["description"],
            candidate_years_experience=cv["years_experience"],
            required_years_experience=selected_job["min_years_experience"],
        )

        if min_final_score is not None and match_result.final_score < min_final_score:
            continue

        ranked_results.append(
            {
                "cv_id": cv["id"],
                "candidate_name": cv["candidate_name"],
                "job_id": selected_job["id"],
                "job_title": selected_job["title"],
                "final_score": match_result.final_score,
                "semantic_score": match_result.semantic_score,
                "skill_score": match_result.skill_score,
                "experience_score": match_result.experience_score,
                "matched_skills": match_result.matched_skills,
                "explanation": match_result.explanation,
            }
        )

    ranked_results.sort(
        key=lambda result: result["final_score"],
        reverse=True,
    )

    return {
        "job_id": selected_job["id"],
        "job_title": selected_job["title"],
        "top_k": top_k,
        "filters": {
            "location": location,
            "min_final_score": min_final_score,
        },
        "results": ranked_results[:top_k],
    }

@router.post("/match/cv/{cv_id}", response_model=CVTopKMatchResponse)
async def match_cv_with_stored_jobs(
    cv_id: int,
    top_k: int = Query(default=5, ge=1, le=20),
    location: str | None = None,
    min_final_score: float | None = Query(default=None, ge=0, le=100),
):
    """
    Match a stored CV with all temporarily stored job postings and return top-k results.
    """

    selected_cv = next(
        (cv for cv in cv_storage if cv["id"] == cv_id),
        None,
    )

    if selected_cv is None:
        raise HTTPException(
            status_code=404,
            detail="CV record not found.",
        )

    if not job_storage:
        raise HTTPException(
            status_code=404,
            detail="No job postings found. Please ingest at least one job posting first.",
        )

    ranked_results = []

    for job in job_storage:
        if location:
            normalized_filter_location = normalize_location(location)
            normalized_job_location = normalize_location(job.get("location"))

            if normalized_job_location != normalized_filter_location:
                continue

        match_result = _build_match_result(
            cv_text=selected_cv["raw_text"],
            job_text=job["description"],
            candidate_years_experience=selected_cv["years_experience"],
            required_years_experience=job["min_years_experience"],
        )

        if min_final_score is not None and match_result.final_score < min_final_score:
            continue

        ranked_results.append(
            {
                "cv_id": selected_cv["id"],
                "candidate_name": selected_cv["candidate_name"],
                "job_id": job["id"],
                "job_title": job["title"],
                "final_score": match_result.final_score,
                "semantic_score": match_result.semantic_score,
                "skill_score": match_result.skill_score,
                "experience_score": match_result.experience_score,
                "matched_skills": match_result.matched_skills,
                "explanation": match_result.explanation,
            }
        )

    ranked_results.sort(
        key=lambda result: result["final_score"],
        reverse=True,
    )

    return CVTopKMatchResponse(
        cv_id=selected_cv["id"],
        candidate_name=selected_cv["candidate_name"],
        top_k=top_k,
        filters={
            "location": location,
            "min_final_score": min_final_score,
        },
        results=ranked_results[:top_k],
    )