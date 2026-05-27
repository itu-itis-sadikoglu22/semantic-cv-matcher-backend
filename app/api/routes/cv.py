from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.cv import CVCreate, CVResponse
from app.services.document_parser import extract_text_from_file
from app.services.ingestion import create_text_preview, normalize_text
from app.services.ner import extract_entities
from app.schemas.common import MessageResponse

router = APIRouter()

# Temporary in-memory storage until PostgreSQL integration is active
cv_storage: list[dict] = []


@router.post("/cvs", response_model=CVResponse)
async def create_cv(cv_data: CVCreate):
    """
    Ingest a CV from raw text and return a normalized preview response.
    """

    normalized_text = normalize_text(cv_data.raw_text)
    extracted_entities = extract_entities(normalized_text)

    cv_id = len(cv_storage) + 1

    cv_record = {
        "id": cv_id,
        "candidate_name": cv_data.candidate_name,
        "email": cv_data.email,
        "phone": cv_data.phone,
        "raw_text": normalized_text,
        "location": cv_data.location,
        "years_experience": cv_data.years_experience,
        "extracted_entities": extracted_entities,
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
        extracted_entities=extracted_entities,
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
            extracted_entities=cv["extracted_entities"],
        )
        for cv in cv_storage
    ]

@router.get("/cvs/{cv_id}", response_model=CVResponse)
async def get_cv_by_id(cv_id: int):
    """
    Get a single CV record by ID from temporary in-memory storage.
    """

    selected_cv = next(
        (cv for cv in cv_storage if cv["id"] == cv_id),
        None,
    )

    if selected_cv is None:
        raise HTTPException(
            status_code=404,
            detail="CV record not found.",
        )

    return CVResponse(
        id=selected_cv["id"],
        candidate_name=selected_cv["candidate_name"],
        email=selected_cv["email"],
        phone=selected_cv["phone"],
        location=selected_cv["location"],
        years_experience=selected_cv["years_experience"],
        raw_text_preview=create_text_preview(selected_cv["raw_text"]),
        extracted_entities=selected_cv["extracted_entities"],
    )

@router.post("/cvs/upload", response_model=CVResponse)
async def upload_cv_file(
    candidate_name: str = Form(...),
    file: UploadFile = File(...),
    email: str | None = Form(default=None),
    phone: str | None = Form(default=None),
    location: str | None = Form(default=None),
    years_experience: float | None = Form(default=None),
):
    """
    Upload a CV file, extract text content, run NER, and return a structured response.
    """

    file_bytes = await file.read()

    try:
        extracted_text = extract_text_from_file(
            file_bytes=file_bytes,
            filename=file.filename or "",
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    normalized_text = normalize_text(extracted_text)

    if not normalized_text:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not contain readable text.",
        )

    extracted_entities = extract_entities(normalized_text)

    cv_id = len(cv_storage) + 1

    cv_record = {
        "id": cv_id,
        "candidate_name": candidate_name,
        "email": email,
        "phone": phone,
        "raw_text": normalized_text,
        "location": location,
        "years_experience": years_experience,
        "extracted_entities": extracted_entities,
    }

    cv_storage.append(cv_record)

    return CVResponse(
        id=cv_id,
        candidate_name=candidate_name,
        email=email,
        phone=phone,
        location=location,
        years_experience=years_experience,
        raw_text_preview=create_text_preview(normalized_text),
        extracted_entities=extracted_entities,
    )

@router.delete("/cvs/{cv_id}", response_model=MessageResponse)
async def delete_cv_by_id(cv_id: int):
    """
    Delete a single CV record by ID from temporary in-memory storage.
    """

    selected_cv = next(
        (cv for cv in cv_storage if cv["id"] == cv_id),
        None,
    )

    if selected_cv is None:
        raise HTTPException(
            status_code=404,
            detail="CV record not found.",
        )

    cv_storage.remove(selected_cv)

    return MessageResponse(
        message=f"CV record with id {cv_id} was deleted successfully."
    )