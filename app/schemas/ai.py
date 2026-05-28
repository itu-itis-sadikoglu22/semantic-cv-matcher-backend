from pydantic import BaseModel, Field

from app.schemas.ner import ExtractedEntities


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


class HybridNERRequest(BaseModel):
    """
    Request schema for hybrid NER extraction.
    """

    text: str = Field(..., min_length=20)


class EntitySourceInfo(BaseModel):
    """
    Explains where an extracted entity came from.
    """

    text: str
    category: str
    source: str
    confidence: float


class HybridNERResponse(BaseModel):
    """
    Response schema for hybrid NER extraction.
    """

    status: str
    extraction_method: str
    rule_based_entities: ExtractedEntities
    transformer_entities: list[TransformerNEREntity]
    merged_entities: ExtractedEntities
    entity_sources: list[EntitySourceInfo]
    notes: list[str]


class AIExtractionMetadata(BaseModel):
    """
    Metadata about the AI extraction method used during ingestion.
    """

    method: str
    status: str
    entity_source_count: int
    notes: list[str]

class NERComparisonRequest(BaseModel):
    """
    Request schema for comparing rule-based and hybrid NER outputs.
    """

    text: str = Field(..., min_length=20)


class NERComparisonResponse(BaseModel):
    """
    Response schema for comparing rule-based and hybrid NER outputs.
    """

    input_preview: str
    rule_based_entities: ExtractedEntities
    hybrid_entities: ExtractedEntities
    added_by_hybrid: ExtractedEntities
    transformer_entities: list[TransformerNEREntity]
    entity_sources: list[EntitySourceInfo]
    explanation: str


class BERTurkEmbeddingRequest(BaseModel):
    text: str = Field(..., min_length=20)


class BERTurkEmbeddingResponse(BaseModel):
    model_name: str
    embedding_dimension: int
    embedding_preview: list[float]
    note: str

class EmbeddingComparisonRequest(BaseModel):
    text: str = Field(..., min_length=20)


class EmbeddingModelPreview(BaseModel):
    model_name: str
    model_type: str
    embedding_dimension: int
    embedding_preview: list[float]


class EmbeddingComparisonResponse(BaseModel):
    input_preview: str
    sentence_transformer: EmbeddingModelPreview
    berturk: EmbeddingModelPreview
    explanation: str