from pydantic import BaseModel, Field


class ExtractedEntities(BaseModel):
    """
    Structured entities extracted from CVs or job postings.
    """

    skills: list[str] = Field(default_factory=list)
    roles: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)