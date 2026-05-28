from fastapi import APIRouter

from app.schemas.ai import (
    AIModelInfo,
    AIModelsResponse,
    HybridNERRequest,
    HybridNERResponse,
    TransformerNERRequest,
    TransformerNERResponse,
)
from app.services.embedding import EMBEDDING_MODEL_NAME
from app.services.transformer_ner import (
    TURKISH_NER_MODEL_NAME,
    extract_transformer_ner_entities,
)
from app.services.hybrid_ner import extract_hybrid_entities

router = APIRouter()


@router.get("/ai/models", response_model=AIModelsResponse)
async def get_ai_models():
    """
    Return information about the AI/NLP components used by the system.
    """

    return AIModelsResponse(
        project_ai_summary=(
            "The backend uses transformer-based sentence embeddings for semantic "
            "CV-job matching, rule-based domain entity extraction for the current "
            "NER fallback, an experimental transformer-based Turkish NER endpoint, "
            "and explainable ranking based on semantic similarity, skill overlap, "
            "and experience compatibility."
        ),
        models=[
            AIModelInfo(
                name=EMBEDDING_MODEL_NAME,
                type="Transformer sentence embedding model",
                purpose=(
                    "Generates dense vector representations for CV and job posting "
                    "texts. These vectors are used to calculate semantic similarity."
                ),
                status="Implemented",
            ),
            AIModelInfo(
                name="Rule-based Turkish CV/Job Entity Extractor",
                type="NER fallback / domain entity extractor",
                purpose=(
                    "Extracts skills, roles, dates, and education-related entities "
                    "from Turkish CV and job posting texts using keyword and pattern "
                    "matching."
                ),
                status="Implemented",
            ),
            AIModelInfo(
                name="Semantic + Skill + Experience Ranking",
                type="Explainable ranking logic",
                purpose=(
                    "Combines semantic similarity score, skill overlap score, and "
                    "experience compatibility score into a final ranking score."
                ),
                status="Implemented",
            ),
            AIModelInfo(
                name=TURKISH_NER_MODEL_NAME,
                type="Transformer token classification model",
                purpose=(
                    "Provides an experimental transformer-based Turkish NER layer "
                    "for extracting named entities from CV and job posting texts."
                ),
                status="Experimental",
            ),
        ],
        planned_improvements=[
            "Merge transformer NER outputs with rule-based domain extraction.",
            "Add confidence/source information for extracted entities.",
            "Persist embeddings in PostgreSQL with pgvector.",
            "Use vector similarity search for scalable retrieval.",
        ],
    )


@router.post("/ai/transformer-ner/extract", response_model=TransformerNERResponse)
async def extract_entities_with_transformer(request: TransformerNERRequest):
    """
    Extract entities using an experimental transformer-based Turkish NER model.
    """

    try:
        entities = extract_transformer_ner_entities(request.text)

        return TransformerNERResponse(
            status="available",
            model_name=TURKISH_NER_MODEL_NAME,
            extraction_method="transformer_token_classification",
            entities=entities,
            error_message=None,
        )

    except Exception as error:
        return TransformerNERResponse(
            status="unavailable",
            model_name=TURKISH_NER_MODEL_NAME,
            extraction_method="transformer_token_classification",
            entities=[],
            error_message=str(error),
        )
    
@router.post("/ai/hybrid-ner/extract", response_model=HybridNERResponse)
async def extract_entities_with_hybrid_ner(request: HybridNERRequest):
    """
    Extract entities using a hybrid rule-based and transformer-based NER pipeline.
    """

    hybrid_result = extract_hybrid_entities(request.text)

    return HybridNERResponse(
        status=hybrid_result["status"],
        extraction_method="hybrid_rule_based_plus_transformer_ner",
        rule_based_entities=hybrid_result["rule_based_entities"],
        transformer_entities=hybrid_result["transformer_entities"],
        merged_entities=hybrid_result["merged_entities"],
        entity_sources=hybrid_result["entity_sources"],
        notes=hybrid_result["notes"],
    )