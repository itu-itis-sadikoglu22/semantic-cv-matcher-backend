from pydantic import BaseModel, Field


class CVCreate(BaseModel):
    """
    Request schema for creating a CV record from raw text.
    """

    candidate_name: str = Field(..., min_length=2, max_length=150)
    email: str | None = Field(default=None, max_length=150)
    phone: str | None = Field(default=None, max_length=50)
    raw_text: str = Field(..., min_length=20)
    location: str | None = Field(default=None, max_length=100)
    years_experience: float | None = Field(default=None, ge=0)


class CVResponse(BaseModel):
    """
    Response schema returned after CV ingestion.
    """

    id: int
    candidate_name: str
    email: str | None
    phone: str | None
    location: str | None
    years_experience: float | None
    raw_text_preview: str