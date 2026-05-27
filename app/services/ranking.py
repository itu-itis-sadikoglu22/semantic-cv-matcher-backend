def calculate_skill_match_score(
    cv_skills: list[str],
    job_skills: list[str],
) -> float:
    """
    Calculate skill overlap score between CV skills and job-required skills.
    """

    if not job_skills:
        return 0.0

    matched_skills = set(cv_skills).intersection(set(job_skills))
    score = len(matched_skills) / len(set(job_skills))

    return round(score * 100, 2)


def calculate_experience_score(
    candidate_years: float | None,
    required_years: float | None,
) -> float:
    """
    Calculate experience compatibility score.
    """

    if required_years is None:
        return 100.0

    if candidate_years is None:
        return 0.0

    if candidate_years >= required_years:
        return 100.0

    score = candidate_years / required_years

    return round(score * 100, 2)


def calculate_final_score(
    semantic_score: float,
    skill_score: float,
    experience_score: float,
) -> float:
    """
    Calculate final weighted ranking score.

    We use a simple explainable weighting strategy:
    - semantic similarity: 60%
    - skill overlap: 30%
    - experience compatibility: 10%
    """

    final_score = (
        semantic_score * 0.60
        + skill_score * 0.30
        + experience_score * 0.10
    )

    return round(final_score, 2)