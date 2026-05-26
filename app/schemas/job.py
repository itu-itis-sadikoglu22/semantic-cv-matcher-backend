from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """
    Request schema for creating a job posting from raw text and metadata.
    """

    title: str = Field(..., min_length=2, max_length=150)
    company_name: str | None = Field(default=None, max_length=150)
    description: str = Field(..., min_length=20)
    location: str | None = Field(default=None, max_length=100)
    seniority: str | None = Field(default=None, max_length=100)
    min_years_experience: float | None = Field(default=None, ge=0)


class JobResponse(BaseModel):
    """
    Response schema returned after job posting ingestion.
    """

    id: int
    title: str
    company_name: str | None
    location: str | None
    seniority: str | None
    min_years_experience: float | None
    description_preview: str