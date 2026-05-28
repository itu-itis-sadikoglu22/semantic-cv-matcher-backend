from collections import Counter

from fastapi import APIRouter

from app.api.routes.cv import cv_storage
from app.api.routes.job import job_storage
from app.schemas.stats import SkillFrequency, StatsSummaryResponse
from app.services.location import normalize_location

router = APIRouter()


def _get_unique_locations(records: list[dict]) -> list[str]:
    """
    Extract unique normalized locations from in-memory records.
    """

    locations = {
        normalize_location(record.get("location"))
        for record in records
        if record.get("location")
    }

    return sorted(locations)


def _get_top_skills(records: list[dict], limit: int = 10) -> list[SkillFrequency]:
    """
    Calculate the most frequent extracted skills from in-memory records.
    """

    skill_counter = Counter()

    for record in records:
        extracted_entities = record.get("extracted_entities")

        if extracted_entities is None:
            continue

        for skill in extracted_entities.skills:
            skill_counter[skill] += 1

    return [
        SkillFrequency(skill=skill, count=count)
        for skill, count in skill_counter.most_common(limit)
    ]


@router.get("/stats/summary", response_model=StatsSummaryResponse)
async def get_stats_summary():
    """
    Return dashboard-style summary statistics for CVs and job postings.
    """

    return StatsSummaryResponse(
        total_cvs=len(cv_storage),
        total_jobs=len(job_storage),
        cv_locations=_get_unique_locations(cv_storage),
        job_locations=_get_unique_locations(job_storage),
        top_cv_skills=_get_top_skills(cv_storage),
        top_job_skills=_get_top_skills(job_storage),
    )