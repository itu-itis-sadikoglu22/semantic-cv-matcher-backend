from fastapi import APIRouter

from app.schemas.ner import NERRequest, NERResponse
from app.services.ner import extract_entities

router = APIRouter()


@router.post("/ner/extract", response_model=NERResponse)
async def extract_ner_entities(request: NERRequest):
    """
    Extract structured entities from CV or job posting text.
    """

    extracted_entities = extract_entities(request.text)

    entity_count = (
        len(extracted_entities.skills)
        + len(extracted_entities.roles)
        + len(extracted_entities.companies)
        + len(extracted_entities.dates)
        + len(extracted_entities.education)
    )

    return NERResponse(
        extraction_method="rule_based_domain_extractor",
        entity_count=entity_count,
        confidence_note=(
            "Current extraction uses a rule-based Turkish CV/job domain extractor. "
            "A transformer-based Turkish NER layer is planned as the next AI improvement."
        ),
        entities=extracted_entities,
    )