from fastapi import APIRouter

from app.schemas.ner import ExtractedEntities, NERRequest
from app.services.ner import extract_entities

router = APIRouter()


@router.post("/ner/extract", response_model=ExtractedEntities)
async def extract_ner_entities(request: NERRequest):
    """
    Extract structured entities from raw CV or job posting text.
    """

    return extract_entities(request.text)