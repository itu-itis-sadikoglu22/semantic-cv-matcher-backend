from pydantic import BaseModel, Field


class AIModelInfo(BaseModel):
    """
    Describes a single AI/NLP component used in the backend.
    """

    name: str
    type: str
    purpose: str
    status: str


class AIModelsResponse(BaseModel):
    """
    Describes the AI/NLP layer of the system.
    """

    project_ai_summary: str
    models: list[AIModelInfo]
    planned_improvements: list[str]

    from pydantic import Field


class TransformerNERRequest(BaseModel):
    """
    Request schema for transformer-based NER extraction.
    """

    text: str = Field(..., min_length=20)


class TransformerNEREntity(BaseModel):
    """
    Single entity detected by the transformer NER model.
    """

    text: str
    label: str
    score: float


class TransformerNERResponse(BaseModel):
    """
    Response schema for experimental transformer-based NER extraction.
    """

    status: str
    model_name: str
    extraction_method: str
    entities: list[TransformerNEREntity]
    error_message: str | None = None

from app.schemas.ner import ExtractedEntities


class HybridNERRequest(BaseModel):
    """
    Request schema for hybrid NER extraction.
    """

    text: str = Field(..., min_length=20)


class HybridNERResponse(BaseModel):
    """
    Response schema for hybrid NER extraction.
    """

    status: str
    extraction_method: str
    rule_based_entities: ExtractedEntities
    transformer_entities: list[TransformerNEREntity]
    merged_entities: ExtractedEntities
    notes: list[str]