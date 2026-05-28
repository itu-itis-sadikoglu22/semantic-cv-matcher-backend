from fastapi import APIRouter

from app.schemas.ai import (
    AIModelInfo,
    AIModelsResponse,
    HybridNERRequest,
    HybridNERResponse,
    TransformerNERRequest,
    TransformerNERResponse,
    NERComparisonRequest,
    NERComparisonResponse,
)
from app.services.embedding import EMBEDDING_MODEL_NAME
from app.services.transformer_ner import (
    TURKISH_NER_MODEL_NAME,
    extract_transformer_ner_entities,
)
from app.services.hybrid_ner import extract_hybrid_entities
from app.services.ner import extract_entities
from app.services.ingestion import create_text_preview

router = APIRouter()


def _calculate_entities_added_by_hybrid(
    rule_based_entities,
    hybrid_entities,
):
    """
    Calculate which entities were added by the hybrid NER pipeline.
    """

    return {
        "skills": sorted(
            set(hybrid_entities.skills) - set(rule_based_entities.skills)
        ),
        "roles": sorted(
            set(hybrid_entities.roles) - set(rule_based_entities.roles)
        ),
        "companies": sorted(
            set(hybrid_entities.companies) - set(rule_based_entities.companies)
        ),
        "dates": sorted(
            set(hybrid_entities.dates) - set(rule_based_entities.dates)
        ),
        "education": sorted(
            set(hybrid_entities.education) - set(rule_based_entities.education)
        ),
    }

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

@router.post("/ai/ner-comparison", response_model=NERComparisonResponse)
async def compare_rule_based_and_hybrid_ner(request: NERComparisonRequest):
    """
    Compare rule-based NER output with hybrid NER output.
    """

    rule_based_entities = extract_entities(request.text)
    hybrid_result = extract_hybrid_entities(request.text)

    hybrid_entities = hybrid_result["merged_entities"]

    added_by_hybrid = _calculate_entities_added_by_hybrid(
        rule_based_entities=rule_based_entities,
        hybrid_entities=hybrid_entities,
    )

    explanation = (
        "This endpoint compares the domain-specific rule-based extractor with "
        "the hybrid NER pipeline. The hybrid pipeline combines rule-based CV/job "
        "entity extraction with transformer-based Turkish NER. The added_by_hybrid "
        "field shows which entities were added by the hybrid approach."
    )

    return NERComparisonResponse(
        input_preview=create_text_preview(request.text),
        rule_based_entities=rule_based_entities,
        hybrid_entities=hybrid_entities,
        added_by_hybrid=added_by_hybrid,
        transformer_entities=hybrid_result["transformer_entities"],
        entity_sources=hybrid_result["entity_sources"],
        explanation=explanation,
    )