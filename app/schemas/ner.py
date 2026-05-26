from pydantic import BaseModel, Field


class NERRequest(BaseModel):
    """
    Request schema for extracting entities from raw text.
    """

    text: str = Field(..., min_length=20)


class ExtractedEntities(BaseModel):
    """
    Structured entities extracted from CVs or job postings.
    """

    skills: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)