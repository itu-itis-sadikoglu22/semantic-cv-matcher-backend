from fastapi import APIRouter

from app.schemas.match import MatchRequest, MatchResponse, MatchResult
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

router = APIRouter()


@router.post("/match/text", response_model=MatchResponse)
async def match_cv_and_job_text(request: MatchRequest):
    """
    Match a CV text and a job posting text using semantic similarity and ranking signals.
    """

    cv_embedding = generate_embedding(request.cv_text)
    job_embedding = generate_embedding(request.job_text)

    similarity_score = calculate_cosine_similarity(cv_embedding, job_embedding)
    semantic_score = calculate_percentage_score(similarity_score)

    cv_entities = extract_entities(request.cv_text)
    job_entities = extract_entities(request.job_text)

    matched_skills = sorted(
        set(cv_entities.skills).intersection(set(job_entities.skills))
    )

    skill_score = calculate_skill_match_score(
        cv_skills=cv_entities.skills,
        job_skills=job_entities.skills,
    )

    experience_score = calculate_experience_score(
        candidate_years=request.candidate_years_experience,
        required_years=request.required_years_experience,
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

    return MatchResponse(
        result=MatchResult(
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
    )