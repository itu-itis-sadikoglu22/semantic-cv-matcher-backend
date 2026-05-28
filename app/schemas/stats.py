from pydantic import BaseModel


class SkillFrequency(BaseModel):
    """
    Represents how often a skill appears in stored CVs or job postings.
    """

    skill: str
    count: int


class StatsSummaryResponse(BaseModel):
    """
    Summary statistics for the current in-memory backend state.
    """

    total_cvs: int
    total_jobs: int
    cv_locations: list[str]
    job_locations: list[str]
    top_cv_skills: list[SkillFrequency]
    top_job_skills: list[SkillFrequency]