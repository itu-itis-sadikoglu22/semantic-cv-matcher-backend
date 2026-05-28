from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.schemas.ai import AIExtractionMetadata
from app.schemas.common import MessageResponse
from app.schemas.job import JobCreate, JobResponse, JobUpdate
from app.services.document_parser import extract_text_from_file
from app.services.hybrid_ner import extract_hybrid_entities
from app.services.ingestion import create_text_preview, normalize_text
from app.services.location import normalize_location

router = APIRouter()

job_storage: list[dict] = []


def get_next_job_id() -> int:
    """
    Generate the next job posting ID based on the current maximum ID in memory.
    """

    if not job_storage:
        return 1

    return max(job["id"] for job in job_storage) + 1


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


@router.post("/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreate):
    """
    Create a temporary job posting record from raw text.
    """

    normalized_description = normalize_text(job_data.description)

    hybrid_result = extract_hybrid_entities(normalized_description)
    extracted_entities = hybrid_result["merged_entities"]
    ai_extraction_metadata = build_ai_extraction_metadata(hybrid_result)

    job_id = get_next_job_id()

    job_record = {
        "id": job_id,
        "title": job_data.title,
        "company_name": job_data.company_name,
        "description": normalized_description,
        "location": job_data.location,
        "seniority": job_data.seniority,
        "min_years_experience": job_data.min_years_experience,
        "extracted_entities": extracted_entities,
        "ai_extraction_metadata": ai_extraction_metadata,
    }

    job_storage.append(job_record)

    return JobResponse(
        id=job_record["id"],
        title=job_record["title"],
        company_name=job_record["company_name"],
        location=job_record["location"],
        seniority=job_record["seniority"],
        min_years_experience=job_record["min_years_experience"],
        description_preview=create_text_preview(normalized_description),
        extracted_entities=extracted_entities,
        ai_extraction_metadata=job_record.get("ai_extraction_metadata"),
    )


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    location: str | None = Query(default=None),
    skill: str | None = Query(default=None),
    seniority: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    List job postings with optional metadata/entity filters.
    """

    filtered_jobs = job_storage.copy()

    if location:
        normalized_filter_location = normalize_location(location)

        filtered_jobs = [
            job
            for job in filtered_jobs
            if normalize_location(job.get("location")) == normalized_filter_location
        ]

    if skill:
        normalized_skill = skill.strip().lower()

        filtered_jobs = [
            job
            for job in filtered_jobs
            if any(
                job_skill.lower() == normalized_skill
                for job_skill in job["extracted_entities"].skills
            )
        ]

    if seniority:
        normalized_seniority = seniority.strip().lower()

        filtered_jobs = [
            job
            for job in filtered_jobs
            if job.get("seniority")
            and job["seniority"].strip().lower() == normalized_seniority
        ]


    if search:
        normalized_search = search.strip().lower()

        filtered_jobs = [
            job
            for job in filtered_jobs
            if normalized_search in job["title"].lower()
            or (
                job.get("company_name") is not None
                and normalized_search in job["company_name"].lower()
            )
            or normalized_search in job["description"].lower()
        ]


    paginated_jobs = filtered_jobs[offset : offset + limit]

    return [
        JobResponse(
            id=job["id"],
            title=job["title"],
            company_name=job["company_name"],
            location=job["location"],
            seniority=job["seniority"],
            min_years_experience=job["min_years_experience"],
            description_preview=create_text_preview(job["description"]),
            extracted_entities=job["extracted_entities"],
            ai_extraction_metadata=job.get("ai_extraction_metadata"),
        )
        for job in paginated_jobs
    ]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_by_id(job_id: int):
    """
    Get a single job posting record by ID from temporary in-memory storage.
    """

    selected_job = next(
        (job for job in job_storage if job["id"] == job_id),
        None,
    )

    if selected_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job posting not found.",
        )

    return JobResponse(
        id=selected_job["id"],
        title=selected_job["title"],
        company_name=selected_job["company_name"],
        location=selected_job["location"],
        seniority=selected_job["seniority"],
        min_years_experience=selected_job["min_years_experience"],
        description_preview=create_text_preview(selected_job["description"]),
        extracted_entities=selected_job["extracted_entities"],
        ai_extraction_metadata=selected_job.get("ai_extraction_metadata"),
    )


@router.patch("/jobs/{job_id}", response_model=JobResponse)
async def update_job_by_id(job_id: int, job_update: JobUpdate):
    """
    Partially update a single job posting by ID.
    """

    selected_job = next(
        (job for job in job_storage if job["id"] == job_id),
        None,
    )

    if selected_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job posting not found.",
        )

    if job_update.title is not None:
        selected_job["title"] = job_update.title

    if job_update.company_name is not None:
        selected_job["company_name"] = job_update.company_name

    if job_update.location is not None:
        selected_job["location"] = job_update.location

    if job_update.seniority is not None:
        selected_job["seniority"] = job_update.seniority

    if job_update.min_years_experience is not None:
        selected_job["min_years_experience"] = job_update.min_years_experience

    if job_update.description is not None:
        normalized_description = normalize_text(job_update.description)

        hybrid_result = extract_hybrid_entities(normalized_description)
        extracted_entities = hybrid_result["merged_entities"]
        ai_extraction_metadata = build_ai_extraction_metadata(hybrid_result)

        selected_job["description"] = normalized_description
        selected_job["extracted_entities"] = extracted_entities
        selected_job["ai_extraction_metadata"] = ai_extraction_metadata

    return JobResponse(
        id=selected_job["id"],
        title=selected_job["title"],
        company_name=selected_job["company_name"],
        location=selected_job["location"],
        seniority=selected_job["seniority"],
        min_years_experience=selected_job["min_years_experience"],
        description_preview=create_text_preview(selected_job["description"]),
        extracted_entities=selected_job["extracted_entities"],
        ai_extraction_metadata=selected_job.get("ai_extraction_metadata"),
    )


@router.post("/jobs/upload", response_model=JobResponse)
async def upload_job_file(
    title: str = Form(...),
    file: UploadFile = File(...),
    company_name: str | None = Form(default=None),
    location: str | None = Form(default=None),
    seniority: str | None = Form(default=None),
    min_years_experience: float | None = Form(default=None),
):
    """
    Upload a job posting file, extract its text, and create a temporary job record.
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

    normalized_description = normalize_text(extracted_text)

    if not normalized_description:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not contain readable text.",
        )

    hybrid_result = extract_hybrid_entities(normalized_description)
    extracted_entities = hybrid_result["merged_entities"]
    ai_extraction_metadata = build_ai_extraction_metadata(hybrid_result)

    job_id = get_next_job_id()

    job_record = {
        "id": job_id,
        "title": title,
        "company_name": company_name,
        "description": normalized_description,
        "location": location,
        "seniority": seniority,
        "min_years_experience": min_years_experience,
        "extracted_entities": extracted_entities,
        "ai_extraction_metadata": ai_extraction_metadata,
    }

    job_storage.append(job_record)

    return JobResponse(
        id=job_record["id"],
        title=job_record["title"],
        company_name=job_record["company_name"],
        location=job_record["location"],
        seniority=job_record["seniority"],
        min_years_experience=job_record["min_years_experience"],
        description_preview=create_text_preview(normalized_description),
        extracted_entities=extracted_entities,
        ai_extraction_metadata=job_record.get("ai_extraction_metadata"),
    )


@router.delete("/jobs/{job_id}", response_model=MessageResponse)
async def delete_job_by_id(job_id: int):
    """
    Delete a single job posting record by ID from temporary in-memory storage.
    """

    selected_job = next(
        (job for job in job_storage if job["id"] == job_id),
        None,
    )

    if selected_job is None:
        raise HTTPException(
            status_code=404,
            detail="Job posting not found.",
        )

    job_storage.remove(selected_job)

    return MessageResponse(
        message=f"Job posting with id {job_id} was deleted successfully."
    )


@router.delete("/jobs", response_model=MessageResponse)
async def clear_all_jobs():
    """
    Delete all job posting records from temporary in-memory storage.
    """

    deleted_count = len(job_storage)
    job_storage.clear()

    return MessageResponse(
        message=f"{deleted_count} job posting record(s) were deleted successfully."
    )