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

class MatchEvidence(BaseModel):
    """
    Explainable evidence used for CV-job matching.
    """

    matched_skills: list[str]
    cv_roles: list[str]
    job_roles: list[str]
    cv_companies: list[str]
    job_companies: list[str]
    cv_education: list[str]
    reason: str

class MatchResult(BaseModel):
    """
    Single semantic matching result with explainable ranking details.
    """

    similarity_score: float
    semantic_score: float
    skill_score: float
    experience_score: float
    final_score: float
    recommendation_level: str
    summary: str
    matched_skills: list[str]
    explanation: str
    cv_entities: ExtractedEntities
    job_entities: ExtractedEntities
    evidence: MatchEvidence


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
    recommendation_level: str
    summary: str
    semantic_score: float
    skill_score: float
    experience_score: float
    matched_skills: list[str]
    explanation: str
    evidence: MatchEvidence


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

class CVTopKMatchResponse(BaseModel):
    """
    Response schema for top-k job matching against a stored CV record.
    """

    cv_id: int
    candidate_name: str
    top_k: int
    filters: MatchFilters
    results: list[TopKMatchItem]