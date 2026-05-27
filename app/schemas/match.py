from pydantic import BaseModel, Field

from app.schemas.ner import ExtractedEntities


class MatchRequest(BaseModel):
    """
    Request schema for semantic matching between a CV text and a job posting text.
    """

    cv_text: str = Field(..., min_length=20)
    job_text: str = Field(..., min_length=20)
    candidate_years_experience: float | None = Field(default=None, ge=0)
    required_years_experience: float | None = Field(default=None, ge=0)


class MatchResult(BaseModel):
    """
    Single semantic matching result with explainable ranking details.
    """

    similarity_score: float
    semantic_score: float
    skill_score: float
    experience_score: float
    final_score: float
    matched_skills: list[str]
    explanation: str
    cv_entities: ExtractedEntities
    job_entities: ExtractedEntities


class MatchResponse(BaseModel):
    """
    Response schema for semantic CV-job matching.
    """

    result: MatchResult

class TopKMatchItem(BaseModel):
    """
    Single ranked CV result for a stored job posting.
    """

    cv_id: int
    candidate_name: str
    job_id: int
    job_title: str
    final_score: float
    semantic_score: float
    skill_score: float
    experience_score: float
    matched_skills: list[str]
    explanation: str


class MatchFilters(BaseModel):
    """
    Metadata filters applied during top-k matching.
    """

    location: str | None
    min_final_score: float | None


class TopKMatchResponse(BaseModel):
    """
    Response schema for top-k matching against stored CV records.
    """

    job_id: int
    job_title: str
    top_k: int
    filters: MatchFilters
    results: list[TopKMatchItem]