from pydantic import BaseModel, Field

from app.schemas.ner import ExtractedEntities


class MatchRequest(BaseModel):
    """
    Request schema for semantic matching between a CV text and a job posting text.
    """

    cv_text: str = Field(..., min_length=20)
    job_text: str = Field(..., min_length=20)


class MatchResult(BaseModel):
    """
    Single semantic matching result with explainable matching details.
    """

    similarity_score: float
    percentage_score: float
    matched_skills: list[str]
    explanation: str
    cv_entities: ExtractedEntities
    job_entities: ExtractedEntities


class MatchResponse(BaseModel):
    """
    Response schema for semantic CV-job matching.
    """

    result: MatchResult