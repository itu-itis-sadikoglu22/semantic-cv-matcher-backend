from fastapi import APIRouter

from app.schemas.match import MatchRequest, MatchResponse, MatchResult
from app.services.embedding import generate_embedding
from app.services.ner import extract_entities
from app.services.similarity import (
    calculate_cosine_similarity,
    calculate_percentage_score,
)

router = APIRouter()


@router.post("/match/text", response_model=MatchResponse)
async def match_cv_and_job_text(request: MatchRequest):
    """
    Match a CV text and a job posting text using semantic similarity.
    """

    cv_embedding = generate_embedding(request.cv_text)
    job_embedding = generate_embedding(request.job_text)

    similarity_score = calculate_cosine_similarity(cv_embedding, job_embedding)
    percentage_score = calculate_percentage_score(similarity_score)

    cv_entities = extract_entities(request.cv_text)
    job_entities = extract_entities(request.job_text)

    matched_skills = sorted(
        set(cv_entities.skills).intersection(set(job_entities.skills))
    )

    explanation = (
        f"The CV and job posting have a semantic match score of "
        f"{percentage_score}%. Matched skills: "
        f"{', '.join(matched_skills) if matched_skills else 'none'}."
    )

    return MatchResponse(
        result=MatchResult(
            similarity_score=round(similarity_score, 4),
            percentage_score=percentage_score,
            matched_skills=matched_skills,
            explanation=explanation,
            cv_entities=cv_entities,
            job_entities=job_entities,
        )
    )