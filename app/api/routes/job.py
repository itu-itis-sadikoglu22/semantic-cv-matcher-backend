from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.job import JobCreate, JobResponse
from app.services.document_parser import extract_text_from_file
from app.services.ingestion import create_text_preview, normalize_text
from app.services.ner import extract_entities

router = APIRouter()

# Temporary in-memory storage until PostgreSQL integration is active
job_storage: list[dict] = []


@router.post("/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreate):
    """
    Ingest a job posting from raw text and metadata.
    """

    normalized_description = normalize_text(job_data.description)
    extracted_entities = extract_entities(normalized_description)

    job_id = len(job_storage) + 1

    job_record = {
        "id": job_id,
        "title": job_data.title,
        "company_name": job_data.company_name,
        "description": normalized_description,
        "location": job_data.location,
        "seniority": job_data.seniority,
        "min_years_experience": job_data.min_years_experience,
        "extracted_entities": extracted_entities,
    }

    job_storage.append(job_record)

    return JobResponse(
        id=job_id,
        title=job_data.title,
        company_name=job_data.company_name,
        location=job_data.location,
        seniority=job_data.seniority,
        min_years_experience=job_data.min_years_experience,
        description_preview=create_text_preview(normalized_description),
        extracted_entities=extracted_entities,
    )


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs():
    """
    Return all ingested job postings from temporary memory storage.
    """

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
        )
        for job in job_storage
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
    Upload a job posting file, extract text content, run NER, and return a structured response.
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

    extracted_entities = extract_entities(normalized_description)

    job_id = len(job_storage) + 1

    job_record = {
        "id": job_id,
        "title": title,
        "company_name": company_name,
        "description": normalized_description,
        "location": location,
        "seniority": seniority,
        "min_years_experience": min_years_experience,
        "extracted_entities": extracted_entities,
    }

    job_storage.append(job_record)

    return JobResponse(
        id=job_id,
        title=title,
        company_name=company_name,
        location=location,
        seniority=seniority,
        min_years_experience=min_years_experience,
        description_preview=create_text_preview(normalized_description),
        extracted_entities=extracted_entities,
    )