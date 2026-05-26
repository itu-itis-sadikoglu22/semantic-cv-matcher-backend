from fastapi import APIRouter

from app.schemas.cv import CVCreate, CVResponse
from app.services.ingestion import create_text_preview, normalize_text

router = APIRouter()

# Temporary in-memory storage until PostgreSQL integration is active
cv_storage: list[dict] = []


@router.post("/cvs", response_model=CVResponse)
async def create_cv(cv_data: CVCreate):
    """
    Ingest a CV from raw text and return a normalized preview response.
    """

    normalized_text = normalize_text(cv_data.raw_text)

    cv_id = len(cv_storage) + 1

    cv_record = {
        "id": cv_id,
        "candidate_name": cv_data.candidate_name,
        "email": cv_data.email,
        "phone": cv_data.phone,
        "raw_text": normalized_text,
        "location": cv_data.location,
        "years_experience": cv_data.years_experience,
    }

    cv_storage.append(cv_record)

    return CVResponse(
        id=cv_id,
        candidate_name=cv_data.candidate_name,
        email=cv_data.email,
        phone=cv_data.phone,
        location=cv_data.location,
        years_experience=cv_data.years_experience,
        raw_text_preview=create_text_preview(normalized_text),
    )


@router.get("/cvs", response_model=list[CVResponse])
async def list_cvs():
    """
    Return all ingested CV records from temporary memory storage.
    """

    return [
        CVResponse(
            id=cv["id"],
            candidate_name=cv["candidate_name"],
            email=cv["email"],
            phone=cv["phone"],
            location=cv["location"],
            years_experience=cv["years_experience"],
            raw_text_preview=create_text_preview(cv["raw_text"]),
        )
        for cv in cv_storage
    ]