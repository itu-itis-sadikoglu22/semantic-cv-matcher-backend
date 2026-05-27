from app.schemas.ner import ExtractedEntities
from app.services.ner import extract_entities
from app.services.transformer_ner import extract_transformer_ner_entities


TECHNICAL_TERMS_TO_EXCLUDE_FROM_COMPANIES = {
    "python",
    "fastapi",
    "postgresql",
    "sql",
    "docker",
    "backend",
    "developer",
    "backend developer",
    "machine learning",
    "deep learning",
    "nlp",
    "react",
    "javascript",
    "git",
}


def _unique_sorted(values: list[str]) -> list[str]:
    """
    Return unique non-empty values sorted alphabetically.
    """

    cleaned_values = {
        value.strip()
        for value in values
        if value and value.strip()
    }

    return sorted(cleaned_values)


def _is_valid_company_candidate(value: str, score: float) -> bool:
    """
    Decide whether a transformer ORG entity is a valid company/organization candidate.
    """

    cleaned_value = value.strip()
    normalized_value = cleaned_value.lower()

    if not cleaned_value:
        return False

    # Ignore subword token artifacts produced by transformer tokenizers.
    if "##" in cleaned_value:
        return False

    # Ignore very short fragments such as "P", "Do", "Back".
    if len(cleaned_value) < 3:
        return False

    # Ignore low-confidence noisy entities.
    if score < 0.80:
        return False

    # Ignore known technical terms that are skills, not companies.
    if normalized_value in TECHNICAL_TERMS_TO_EXCLUDE_FROM_COMPANIES:
        return False

    # Ignore single generic words that are usually not organizations in this domain.
    if normalized_value in {"mühendisliği", "engineering", "developer"}:
        return False

    return True


def extract_hybrid_entities(text: str) -> dict:
    """
    Combine rule-based domain extraction with transformer-based NER.

    Rule-based extraction is used for domain-specific CV/job entities such as
    skills, roles, dates, and education.

    Transformer NER is used as an additional source for named entities,
    especially organizations/companies.
    """

    rule_based_entities = extract_entities(text)

    notes = [
        "Rule-based extractor is used for domain-specific CV/job entities.",
    ]

    transformer_entities = []
    transformer_status = "available"

    try:
        transformer_entities = extract_transformer_ner_entities(text)
        notes.append("Transformer NER was executed successfully.")

    except Exception as error:
        transformer_status = "unavailable"
        notes.append(
            f"Transformer NER could not be executed. Fallback reason: {error}"
        )

    transformer_companies = [
        entity["text"]
        for entity in transformer_entities
        if entity["label"].upper() in {"ORG", "ORGANIZATION"}
        and _is_valid_company_candidate(
            value=entity["text"],
            score=entity["score"],
        )
    ]

    merged_entities = ExtractedEntities(
        skills=_unique_sorted(rule_based_entities.skills),
        roles=_unique_sorted(rule_based_entities.roles),
        companies=_unique_sorted(
            rule_based_entities.companies + transformer_companies
        ),
        dates=_unique_sorted(rule_based_entities.dates),
        education=_unique_sorted(rule_based_entities.education),
    )

    return {
        "status": transformer_status,
        "rule_based_entities": rule_based_entities,
        "transformer_entities": transformer_entities,
        "merged_entities": merged_entities,
        "notes": notes,
    }