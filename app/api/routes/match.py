from fastapi import APIRouter, HTTPException, Query

from app.api.routes.cv import cv_storage
from app.api.routes.job import job_storage
from app.schemas.match import (
    CVTopKMatchResponse,
    MatchEvidence,
    MatchRequest,
    MatchResponse,
    MatchResult,
    TopKMatchResponse,
)
from app.schemas.ner import ExtractedEntities
from app.services.embedding import generate_embedding
from app.services.hybrid_ner import extract_hybrid_entities
from app.services.location import normalize_location
from app.services.ranking import (
    calculate_experience_score,
    calculate_final_score,
    calculate_skill_match_score,
)
from app.services.similarity import (
    calculate_cosine_similarity,
    calculate_percentage_score,
)

router = APIRouter()


def _extract_entities_for_matching(text: str) -> ExtractedEntities:
    """
    Extract entities for matching by using the hybrid NER pipeline.
    """

    hybrid_result = extract_hybrid_entities(text)
    return hybrid_result["merged_entities"]


def _build_match_evidence(
    cv_entities: ExtractedEntities,
    job_entities: ExtractedEntities,
    matched_skills: list[str],
    final_score: float,
) -> MatchEvidence:
    """
    Build explainable evidence for a CV-job match.
    """

    role_overlap = sorted(
        set(cv_entities.roles).intersection(set(job_entities.roles))
    )

    if matched_skills and role_overlap:
        reason = (
            "The candidate is a strong match because the CV and job posting share "
            "important technical skills and compatible role information."
        )
    elif matched_skills:
        reason = (
            "The candidate matches the job mainly because there is a strong overlap "
            "between the required and detected technical skills."
        )
    elif final_score >= 70:
        reason = (
            "The candidate has a good semantic match with the job posting, although "
            "explicit skill overlap is limited."
        )
    else:
        reason = (
            "The candidate has limited evidence for this job based on the current "
            "semantic, skill, and experience signals."
        )

    return MatchEvidence(
        matched_skills=matched_skills,
        cv_roles=cv_entities.roles,
        job_roles=job_entities.roles,
        cv_companies=cv_entities.companies,
        job_companies=job_entities.companies,
        cv_education=cv_entities.education,
        reason=reason,
    )


def _build_match_result(
    cv_text: str,
    job_text: str,
    candidate_years_experience: float | None = None,
    required_years_experience: float | None = None,
    cv_entities_override: ExtractedEntities | None = None,
    job_entities_override: ExtractedEntities | None = None,
) -> MatchResult:
    """
    Build a semantic and explainable match result for one CV-job pair.
    """

    cv_embedding = generate_embedding(cv_text)
    job_embedding = generate_embedding(job_text)

    similarity_score = calculate_cosine_similarity(cv_embedding, job_embedding)
    semantic_score = calculate_percentage_score(similarity_score)

    cv_entities = cv_entities_override or _extract_entities_for_matching(cv_text)
    job_entities = job_entities_override or _extract_entities_for_matching(job_text)

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

    evidence = _build_match_evidence(
        cv_entities=cv_entities,
        job_entities=job_entities,
        matched_skills=matched_skills,
        final_score=final_score,
    )

    explanation = (
        f"The CV and job posting have a semantic score of {semantic_score}%. "
        f"The skill match score is {skill_score}%, and the experience score is "
        f"{experience_score}%. The final weighted ranking score is {final_score}%. "
        f"Matched skills: {', '.join(matched_skills) if matched_skills else 'none'}. "
        f"Evidence summary: {evidence.reason}"
    )

    return MatchResult(
        similarity_score=round(similarity_score, 4),
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
        final_score=final_score,
        matched_skills=matched_skills,
        explanation=explanation,
        evidence=evidence,
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
            cv_entities_override=cv["extracted_entities"],
            job_entities_override=selected_job["extracted_entities"],
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
                "evidence": match_result.evidence,
            }
        )

    ranked_results.sort(
        key=lambda result: result["final_score"],
        reverse=True,
    )

    return TopKMatchResponse(
        job_id=selected_job["id"],
        job_title=selected_job["title"],
        top_k=top_k,
        filters={
            "location": location,
            "min_final_score": min_final_score,
        },
        results=ranked_results[:top_k],
    )


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
            cv_entities_override=selected_cv["extracted_entities"],
            job_entities_override=job["extracted_entities"],
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
                "evidence": match_result.evidence,
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