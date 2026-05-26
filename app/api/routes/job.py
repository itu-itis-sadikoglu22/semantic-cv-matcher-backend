from fastapi import APIRouter

from app.schemas.job import JobCreate, JobResponse
from app.services.ingestion import create_text_preview, normalize_text

router = APIRouter()

# Temporary in-memory storage until PostgreSQL integration is active
job_storage: list[dict] = []


@router.post("/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreate):
    """
    Ingest a job posting from raw text and metadata.
    """

    normalized_description = normalize_text(job_data.description)

    job_id = len(job_storage) + 1

    job_record = {
        "id": job_id,
        "title": job_data.title,
        "company_name": job_data.company_name,
        "description": normalized_description,
        "location": job_data.location,
        "seniority": job_data.seniority,
        "min_years_experience": job_data.min_years_experience,
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
        )
        for job in job_storage
    ]