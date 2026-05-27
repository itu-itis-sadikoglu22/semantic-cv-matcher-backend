from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.schemas.common import MessageResponse
from app.schemas.cv import CVCreate, CVResponse
from app.services.document_parser import extract_text_from_file
from app.services.ingestion import create_text_preview, normalize_text
from app.services.location import normalize_location
from app.services.ner import extract_entities

router = APIRouter()

# Temporary in-memory storage until PostgreSQL integration is active
cv_storage: list[dict] = []
def get_next_cv_id() -> int:
    """
    Generate the next CV ID based on the current maximum ID in memory.
    """

    if not cv_storage:
        return 1

    return max(cv["id"] for cv in cv_storage) + 1

@router.post("/cvs", response_model=CVResponse)
async def create_cv(cv_data: CVCreate):
    """
    Ingest a CV from raw text and return a normalized preview response.
    """

    normalized_text = normalize_text(cv_data.raw_text)
    extracted_entities = extract_entities(normalized_text)

    cv_id = get_next_cv_id()

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
async def list_cvs(
    location: str | None = Query(default=None),
    skill: str | None = Query(default=None),
):
    """
    List CV records with optional metadata/entity filters.
    """

    filtered_cvs = cv_storage.copy()

    if location:
        normalized_filter_location = normalize_location(location)

        filtered_cvs = [
            cv
            for cv in filtered_cvs
            if normalize_location(cv.get("location")) == normalized_filter_location
        ]

    if skill:
        normalized_skill = skill.strip().lower()

        filtered_cvs = [
            cv
            for cv in filtered_cvs
            if any(
                cv_skill.lower() == normalized_skill
                for cv_skill in cv["extracted_entities"].skills
            )
        ]

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
        for cv in filtered_cvs
    ]

@router.get("/cvs", response_model=list[CVResponse])
async def list_cvs(
    location: str | None = None,
    skill: str | None = Query(default=None),
):
    """
    List CV records with optional metadata/entity filters.
    """

    filtered_cvs = cv_storage

    if location:
        normalized_filter_location = normalize_location(location)

        filtered_cvs = [
            cv for cv in filtered_cvs
            if normalize_location(cv.get("location")) == normalized_filter_location
        ]

    if skill:
        normalized_skill = skill.strip().lower()

        filtered_cvs = [
            cv for cv in filtered_cvs
            if any(
                cv_skill.lower() == normalized_skill
                for cv_skill in cv["extracted_entities"].skills
            )
        ]

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
        for cv in filtered_cvs
    ]

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

    cv_id = get_next_cv_id()
    
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

@router.delete("/cvs", response_model=MessageResponse)
async def clear_all_cvs():
    """
    Delete all CV records from temporary in-memory storage.
    """

    deleted_count = len(cv_storage)
    cv_storage.clear()

    return MessageResponse(
        message=f"{deleted_count} CV record(s) were deleted successfully."
    )