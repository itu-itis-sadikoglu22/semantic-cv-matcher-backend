from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.schemas.ai import AIExtractionMetadata
from app.schemas.common import MessageResponse
from app.schemas.cv import CVCreate, CVResponse, CVUpdate 
from app.services.document_parser import extract_text_from_file
from app.services.hybrid_ner import extract_hybrid_entities
from app.services.ingestion import create_text_preview, normalize_text
from app.services.location import normalize_location

router = APIRouter()

cv_storage: list[dict] = []


def get_next_cv_id() -> int:
    """
    Generate the next CV ID based on the current maximum ID in memory.
    """

    if not cv_storage:
        return 1

    return max(cv["id"] for cv in cv_storage) + 1


def build_ai_extraction_metadata(hybrid_result: dict) -> AIExtractionMetadata:
    """
    Build AI extraction metadata from hybrid NER result.
    """

    return AIExtractionMetadata(
        method="hybrid_rule_based_plus_transformer_ner",
        status=hybrid_result["status"],
        entity_source_count=len(hybrid_result["entity_sources"]),
        notes=hybrid_result["notes"],
    )


@router.post("/cvs", response_model=CVResponse)
async def create_cv(cv_data: CVCreate):
    """
    Create a temporary CV record from raw text.
    """

    normalized_text = normalize_text(cv_data.raw_text)

    hybrid_result = extract_hybrid_entities(normalized_text)
    extracted_entities = hybrid_result["merged_entities"]
    ai_extraction_metadata = build_ai_extraction_metadata(hybrid_result)

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
        "ai_extraction_metadata": ai_extraction_metadata,
    }

    cv_storage.append(cv_record)

    return CVResponse(
        id=cv_record["id"],
        candidate_name=cv_record["candidate_name"],
        email=cv_record["email"],
        phone=cv_record["phone"],
        location=cv_record["location"],
        years_experience=cv_record["years_experience"],
        raw_text_preview=create_text_preview(normalized_text),
        extracted_entities=extracted_entities,
        ai_extraction_metadata=cv_record.get("ai_extraction_metadata"),
    )


@router.get("/cvs", response_model=list[CVResponse])
async def list_cvs(
    location: str | None = Query(default=None),
    skill: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    List CV records with optional metadata/entity filters and pagination.
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

    if search:
        normalized_search = search.strip().lower()

        filtered_cvs = [
            cv
            for cv in filtered_cvs
            if normalized_search in cv["candidate_name"].lower()
            or (
                cv.get("email") is not None
                and normalized_search in cv["email"].lower()
            )
            or normalized_search in cv["raw_text"].lower()
        ]


    paginated_cvs = filtered_cvs[offset : offset + limit]

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
            ai_extraction_metadata=cv.get("ai_extraction_metadata"),
        )
        for cv in paginated_cvs
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
        ai_extraction_metadata=selected_cv.get("ai_extraction_metadata"),
    )

@router.patch("/cvs/{cv_id}", response_model=CVResponse)
async def update_cv_by_id(cv_id: int, cv_update: CVUpdate):
    """
    Partially update a single CV record by ID.
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

    if cv_update.candidate_name is not None:
        selected_cv["candidate_name"] = cv_update.candidate_name

    if cv_update.email is not None:
        selected_cv["email"] = cv_update.email

    if cv_update.phone is not None:
        selected_cv["phone"] = cv_update.phone

    if cv_update.location is not None:
        selected_cv["location"] = cv_update.location

    if cv_update.years_experience is not None:
        selected_cv["years_experience"] = cv_update.years_experience

    if cv_update.raw_text is not None:
        normalized_text = normalize_text(cv_update.raw_text)

        hybrid_result = extract_hybrid_entities(normalized_text)
        extracted_entities = hybrid_result["merged_entities"]
        ai_extraction_metadata = build_ai_extraction_metadata(hybrid_result)

        selected_cv["raw_text"] = normalized_text
        selected_cv["extracted_entities"] = extracted_entities
        selected_cv["ai_extraction_metadata"] = ai_extraction_metadata

    return CVResponse(
        id=selected_cv["id"],
        candidate_name=selected_cv["candidate_name"],
        email=selected_cv["email"],
        phone=selected_cv["phone"],
        location=selected_cv["location"],
        years_experience=selected_cv["years_experience"],
        raw_text_preview=create_text_preview(selected_cv["raw_text"]),
        extracted_entities=selected_cv["extracted_entities"],
        ai_extraction_metadata=selected_cv.get("ai_extraction_metadata"),
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
    Upload a CV file, extract its text, and create a temporary CV record.
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

    hybrid_result = extract_hybrid_entities(normalized_text)
    extracted_entities = hybrid_result["merged_entities"]
    ai_extraction_metadata = build_ai_extraction_metadata(hybrid_result)

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
        "ai_extraction_metadata": ai_extraction_metadata,
    }

    cv_storage.append(cv_record)

    return CVResponse(
        id=cv_record["id"],
        candidate_name=cv_record["candidate_name"],
        email=cv_record["email"],
        phone=cv_record["phone"],
        location=cv_record["location"],
        years_experience=cv_record["years_experience"],
        raw_text_preview=create_text_preview(normalized_text),
        extracted_entities=extracted_entities,
        ai_extraction_metadata=cv_record.get("ai_extraction_metadata"),
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

    