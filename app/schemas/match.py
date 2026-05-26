from pydantic import BaseModel, Field

from app.schemas.ner import ExtractedEntities


class MatchRequest(BaseModel):
    """
    Request schema for retrieving top-k matching CVs for a job posting.
    """

    job_id: int
    top_k: int = Field(default=10, ge=1, le=50)
    location: str | None = None
    min_years_experience: float | None = Field(default=None, ge=0)


class MatchResult(BaseModel):
    """
    Single ranked candidate result with explainable matching details.
    """

    cv_id: int
    candidate_name: str
    similarity_score: float
    final_score: float
    matched_skills: list[str]
    explanation: str
    extracted_entities: ExtractedEntities


class MatchResponse(BaseModel):
    """
    Response schema for ranked CV matching results.
    """

    job_id: int
    results: list[MatchResult]