import re

from app.schemas.ner import ExtractedEntities


SKILL_KEYWORDS = [
    "Python",
    "FastAPI",
    "PostgreSQL",
    "SQL",
    "Docker",
    "Machine Learning",
    "Makine Öğrenmesi",
    "Deep Learning",
    "Derin Öğrenme",
    "NLP",
    "Natural Language Processing",
    "React",
    "JavaScript",
    "Java",
    "C++",
    "Git",
    "REST API",
]

ROLE_KEYWORDS = [
    "Backend Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Software Engineer",
    "Data Scientist",
    "Machine Learning Engineer",
    "ML Engineer",
    "AI Engineer",
    "Computer Engineer",
    "Bilgisayar Mühendisi",
]

EDUCATION_KEYWORDS = [
    "Computer Engineering",
    "Bilgisayar Mühendisliği",
    "Software Engineering",
    "Yazılım Mühendisliği",
    "B.Sc.",
    "M.Sc.",
    "Lisans",
    "Yüksek Lisans",
]


def _find_keyword_matches(text: str, keywords: list[str]) -> list[str]:
    """
    Find keyword-based entity matches in a case-insensitive way.
    """

    matches = []

    for keyword in keywords:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)

        if pattern.search(text):
            matches.append(keyword)

    return sorted(set(matches))


def _extract_dates(text: str) -> list[str]:
    """
    Extract simple date and duration expressions from Turkish or English text.
    """

    date_patterns = [
        r"\b\d{4}\s*-\s*\d{4}\b",
        r"\b\d{4}\b",
        r"\b\d+\s*yıl\b",
        r"\b\d+\s*years?\b",
    ]

    dates = []

    for pattern in date_patterns:
        dates.extend(re.findall(pattern, text, flags=re.IGNORECASE))

    return sorted(set(dates))


def extract_entities(text: str) -> ExtractedEntities:
    """
    Extract structured entities from raw CV or job posting text.
    """

    skills = _find_keyword_matches(text, SKILL_KEYWORDS)
    roles = _find_keyword_matches(text, ROLE_KEYWORDS)
    education = _find_keyword_matches(text, EDUCATION_KEYWORDS)
    dates = _extract_dates(text)

    return ExtractedEntities(
        skills=skills,
        roles=roles,
        companies=[],
        dates=dates,
        education=education,
    )