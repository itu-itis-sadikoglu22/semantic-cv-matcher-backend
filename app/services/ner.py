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
    "java",
    "spring boot",
    "kubernetes",
    "microservice",
    "microservices",
    "rest api",
    "api",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "nodejs",
    "django",
    "flask",
    "mysql",
    "mongodb",
    "redis",
    "git",
    "github",
    "linux",
    "html",
    "css",
    "js",
    "node js",
    "postgres",
    "postgres sql",
    "k8s",
    "restful api",
    "micro-service",
    "micro services",
]


SKILL_NORMALIZATION_MAP = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "postgres sql": "PostgreSQL",
    "sql": "SQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "rest api": "REST API",
    "restful api": "REST API",
    "api": "API",
    "microservice": "Microservice",
    "microservices": "Microservice",
    "micro-service": "Microservice",
    "micro services": "Microservice",
    "python": "Python",
    "java": "Java",
    "spring boot": "Spring Boot",
    "fastapi": "FastAPI",
    "docker": "Docker",
    "git": "Git",
    "github": "GitHub",
    "react": "React",
    "django": "Django",
    "flask": "Flask",
    "linux": "Linux",
    "html": "HTML",
    "css": "CSS",
}


def normalize_skill_name(skill: str) -> str:
    """
    Normalize skill aliases into a consistent display name.
    """

    normalized_skill = skill.strip().lower()

    return SKILL_NORMALIZATION_MAP.get(
        normalized_skill,
        skill.strip(),
    )


ROLE_KEYWORDS = [
    "Backend Developer",
    "Backend Engineer",
    "Frontend Developer",
    "Frontend Engineer",
    "Full Stack Developer",
    "Full Stack Engineer",
    "Software Engineer",
    "Software Developer",
    "Data Scientist",
    "Data Engineer",
    "Machine Learning Engineer",
    "ML Engineer",
    "AI Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "QA Engineer",
    "Test Engineer",
    "Mobile Developer",
    "Android Developer",
    "iOS Developer",
    "Computer Engineer",
    "Bilgisayar Mühendisi",
    "Yazılım Mühendisi",
    "Veri Bilimci",
    "Veri Mühendisi",
    "Makine Öğrenmesi Mühendisi",
    "Yapay Zeka Mühendisi",
    "Mobil Geliştirici",
    "Test Mühendisi",
    "DevOps Mühendisi",
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
    Extract simple date and experience duration expressions from Turkish or English text.
    """

    date_patterns = [
        r"\b\d{4}\s*-\s*\d{4}\b",
        r"\b\d{4}\b",

        # Turkish experience expressions
        r"\b\d+\s*yıl\b",
        r"\b\d+\s*\+\s*yıl\b",
        r"\ben az\s+\d+\s*yıl\b",
        r"\bminimum\s+\d+\s*yıl\b",
        r"\b\d+\s*yıl\s*üzeri\b",
        r"\b\d+\s*yıldan\s*fazla\b",

        # English experience expressions
        r"\b\d+\s*years?\b",
        r"\b\d+\s*\+\s*years?\b",
        r"\bat least\s+\d+\s*years?\b",
        r"\bminimum\s+\d+\s*years?\b",
        r"\bmore than\s+\d+\s*years?\b",
    ]

    dates = []

    for pattern in date_patterns:
        dates.extend(re.findall(pattern, text, flags=re.IGNORECASE))

    unique_dates = sorted(set(date.strip() for date in dates))

    filtered_dates = []

    for date in unique_dates:
        is_part_of_longer_expression = any(
            date != other_date and date.lower() in other_date.lower()
            for other_date in unique_dates
        )

        if not is_part_of_longer_expression:
            filtered_dates.append(date)

    return filtered_dates


def extract_entities(text: str) -> ExtractedEntities:
    """
    Extract structured entities from raw CV or job posting text.
    """

    raw_skills = _find_keyword_matches(text, SKILL_KEYWORDS)
    skills = sorted(
        set(
            normalize_skill_name(skill)
            for skill in raw_skills
        )
    )
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