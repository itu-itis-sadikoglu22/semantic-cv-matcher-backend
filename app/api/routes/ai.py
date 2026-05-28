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
    BERTurkEmbeddingRequest,
    BERTurkEmbeddingResponse,
)
from app.services.embedding import EMBEDDING_MODEL_NAME
from app.services.transformer_ner import (
    TURKISH_NER_MODEL_NAME,
    extract_transformer_ner_entities,
)
from app.services.hybrid_ner import extract_hybrid_entities
from app.services.ner import extract_entities
from app.services.ingestion import create_text_preview
from app.services.berturk_embedding import (
    BERTURK_MODEL_NAME,
    generate_berturk_embedding,
)

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
    Return the AI/NLP model registry used in the project.
    """

    return AIModelsResponse(
        project_ai_summary=(
            "This backend uses a hybrid AI/NLP architecture for Turkish CV and "
            "job matching. It combines rule-based entity extraction, transformer-based "
            "Turkish NER, multilingual sentence embeddings, semantic similarity, "
            "and explainable ranking."
        ),
        models=[
            AIModelInfo(
                name=EMBEDDING_MODEL_NAME,
                type="sentence-transformer",
                purpose=(
                    "Generates dense multilingual embeddings for CV and job texts. "
                    "Used for semantic similarity and ranking."
                ),
                status="active",
            ),
            AIModelInfo(
                name=TURKISH_NER_MODEL_NAME,
                type="transformer-token-classification",
                purpose=(
                    "Extracts Turkish named entities such as organizations and locations. "
                    "Used inside the hybrid NER pipeline."
                ),
                status="active",
            ),
            AIModelInfo(
                name="Rule-based CV/Job Entity Extractor",
                type="rule-based-nlp",
                purpose=(
                    "Extracts domain-specific CV/job entities such as skills, roles, "
                    "education, experience durations and technical keywords."
                ),
                status="active",
            ),
            AIModelInfo(
                name="Hybrid NER Pipeline",
                type="hybrid-ai-pipeline",
                purpose=(
                    "Combines rule-based extraction with transformer-based Turkish NER. "
                    "Used during CV ingestion, job ingestion, file upload and update operations."
                ),
                status="active",
            ),
            AIModelInfo(
                name="dbmdz/bert-base-turkish-cased",
                type="berturk-transformer-encoder",
                purpose=(
                    "Planned experimental Turkish BERT encoder for comparing Turkish text "
                    "representations with the current sentence-transformer embedding model."
                ),
                status="planned",
            ),
            AIModelInfo(
                name="PostgreSQL pgvector with HNSW",
                type="vector-database-search",
                purpose=(
                    "Planned storage and approximate nearest neighbor search layer for "
                    "persistent semantic CV-job matching."
                ),
                status="planned",
            ),
        ],
        planned_improvements=[
            "Add experimental BERTurk embedding endpoint.",
            "Add sentence-transformer vs BERTurk comparison endpoint.",
            "Persist CV and job embeddings in PostgreSQL with pgvector.",
            "Add HNSW index for faster vector similarity search.",
            "Improve skill, role, education and experience extraction.",
            "Add AI evaluation examples for final project demo.",
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

@router.post("/ai/berturk-embedding", response_model=BERTurkEmbeddingResponse)
async def generate_experimental_berturk_embedding(
    request: BERTurkEmbeddingRequest,
):
    """
    Generate an experimental BERTurk embedding for a Turkish text.
    """

    embedding = generate_berturk_embedding(request.text)

    return BERTurkEmbeddingResponse(
        model_name=BERTURK_MODEL_NAME,
        embedding_dimension=len(embedding),
        embedding_preview=embedding[:10],
        note=(
            "This endpoint is experimental. The main matching pipeline currently "
            "uses the sentence-transformer embedding model, while BERTurk is added "
            "for Turkish representation experiments and comparison."
        ),
    )