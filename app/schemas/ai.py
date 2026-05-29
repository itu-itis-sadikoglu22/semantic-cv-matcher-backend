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

class AIMatchingEvaluationRequest(BaseModel):
    cv_text: str = Field(..., min_length=20)
    job_text: str = Field(..., min_length=20)
    candidate_years_experience: float | None = Field(default=None, ge=0)
    required_years_experience: float | None = Field(default=None, ge=0)
    critical_skills: list[str] = Field(default_factory=list)

class AIScoreBreakdown(BaseModel):
    semantic_weight: float
    skill_weight: float
    experience_weight: float
    semantic_contribution: float
    skill_contribution: float
    experience_contribution: float


class AIEvaluationMetadata(BaseModel):
    evaluation_method: str
    semantic_model: str
    entity_extraction_method: str
    ranking_strategy: str
    explainability_features: list[str]


class AIMatchingEvaluationResponse(BaseModel):
    semantic_score: float
    skill_score: float
    experience_score: float
    final_score: float
    recommendation_level: str
    matched_skills: list[str]
    missing_skills: list[str]
    missing_critical_skills: list[str]
    cv_entities: ExtractedEntities
    job_entities: ExtractedEntities
    strengths: list[str]
    weaknesses: list[str]
    ai_comment: str
    score_breakdown: AIScoreBreakdown
    confidence_level: str
    risk_flags: list[str]
    evaluation_metadata: AIEvaluationMetadata


class AIDemoTestCase(BaseModel):
    case_id: str
    title: str
    description: str
    cv_text: str
    job_text: str
    candidate_years_experience: float
    required_years_experience: float
    critical_skills: list[str]
    expected_result: str


class AIDemoTestCasesResponse(BaseModel):
    purpose: str
    test_cases: list[AIDemoTestCase]

class NEREvaluationExpectedEntities(BaseModel):
    skills: list[str]
    roles: list[str]
    companies: list[str]
    dates: list[str]
    education: list[str]


class NEREvaluationTestCase(BaseModel):
    case_id: str
    title: str
    text: str
    expected_entities: NEREvaluationExpectedEntities


class NEREvaluationDatasetResponse(BaseModel):
    purpose: str
    evaluation_note: str
    test_cases: list[NEREvaluationTestCase]