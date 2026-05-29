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
    EmbeddingComparisonRequest,
    EmbeddingComparisonResponse,
    EmbeddingModelPreview,
    AIMatchingEvaluationRequest,
    AIMatchingEvaluationResponse,
    AIScoreBreakdown,
)
from app.services.embedding import EMBEDDING_MODEL_NAME, generate_embedding
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
from app.services.ranking import calculate_final_score
from app.services.similarity import calculate_cosine_similarity
from app.services.ner import extract_entities

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


def _get_recommendation_level_for_ai(final_score: float) -> str:
    """
    Convert final score into a recommendation level.
    """

    if final_score >= 85:
        return "STRONG_MATCH"

    if final_score >= 70:
        return "GOOD_MATCH"

    if final_score >= 50:
        return "POSSIBLE_MATCH"

    return "WEAK_MATCH"


def _build_ai_strengths(
    matched_skills: list[str],
    semantic_score: float,
    experience_score: float,
) -> list[str]:
    """
    Build human-readable strengths for a matching result.
    """

    strengths = []

    if semantic_score >= 70:
        strengths.append("The CV and job description are semantically similar.")

    if matched_skills:
        strengths.append(
            f"The candidate matches {len(matched_skills)} required skill(s)."
        )

    if experience_score >= 80:
        strengths.append("The candidate meets the experience expectation.")

    return strengths


def _build_ai_weaknesses(
    matched_skills: list[str],
    job_skill_count: int,
    semantic_score: float,
    experience_score: float,
) -> list[str]:
    """
    Build human-readable weaknesses for a matching result.
    """

    weaknesses = []

    if semantic_score < 50:
        weaknesses.append("The semantic similarity between CV and job text is low.")

    if job_skill_count > 0 and len(matched_skills) < job_skill_count:
        missing_count = job_skill_count - len(matched_skills)
        weaknesses.append(
            f"The candidate is missing {missing_count} detected required skill(s)."
        )

    if experience_score < 80:
        weaknesses.append("The candidate may not fully meet the experience expectation.")

    return weaknesses


def _build_ai_comment(final_score: float, recommendation_level: str) -> str:
    """
    Build a short AI-style evaluation comment.
    """

    if recommendation_level == "STRONG_MATCH":
        return (
            f"The candidate is a strong fit for this role with a final score of "
            f"{final_score}."
        )

    if recommendation_level == "GOOD_MATCH":
        return (
            f"The candidate is a good fit, but there may still be minor gaps. "
            f"Final score: {final_score}."
        )

    if recommendation_level == "POSSIBLE_MATCH":
        return (
            f"The candidate may be suitable, but the match requires further review. "
            f"Final score: {final_score}."
        )

    return (
        f"The candidate appears to be a weak match for this role. "
        f"Final score: {final_score}."
    )


def _calculate_skill_score_for_ai(
    cv_skills: list[str],
    job_skills: list[str],
) -> float:
    """
    Calculate skill overlap score between CV skills and job skills.
    """

    if not job_skills:
        return 100.0

    matched_skills = set(cv_skills).intersection(set(job_skills))

    return round(
        (len(matched_skills) / len(set(job_skills))) * 100,
        2,
    )


def _build_score_breakdown(
    semantic_score: float,
    skill_score: float,
    experience_score: float,
) -> AIScoreBreakdown:
    """
    Build an explainable weighted score breakdown for AI matching evaluation.
    """

    semantic_weight = 0.60
    skill_weight = 0.30
    experience_weight = 0.10

    return AIScoreBreakdown(
        semantic_weight=semantic_weight,
        skill_weight=skill_weight,
        experience_weight=experience_weight,
        semantic_contribution=round(semantic_score * semantic_weight, 2),
        skill_contribution=round(skill_score * skill_weight, 2),
        experience_contribution=round(experience_score * experience_weight, 2),
    )


def _get_confidence_level_for_ai(
    semantic_score: float,
    skill_score: float,
    experience_score: float,
    job_skill_count: int,
) -> str:
    """
    Estimate confidence level for the AI matching evaluation.
    """

    if job_skill_count == 0:
        return "LOW"

    if semantic_score >= 70 and skill_score >= 60 and experience_score >= 80:
        return "HIGH"

    if semantic_score >= 50 and skill_score >= 40:
        return "MEDIUM"

    return "LOW"

def _build_risk_flags_for_ai(
    semantic_score: float,
    skill_score: float,
    experience_score: float,
    missing_skills: list[str],
) -> list[str]:
    """
    Build risk flags for AI matching evaluation.
    """

    risk_flags = []

    if semantic_score < 50:
        risk_flags.append("LOW_SEMANTIC_SIMILARITY")

    if skill_score < 50:
        risk_flags.append("LOW_SKILL_OVERLAP")

    if experience_score < 80:
        risk_flags.append("EXPERIENCE_GAP")

    if len(missing_skills) >= 3:
        risk_flags.append("MISSING_CRITICAL_SKILLS")

    if not risk_flags:
        risk_flags.append("NO_MAJOR_RISK_DETECTED")

    return risk_flags

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


@router.post("/ai/embedding-comparison", response_model=EmbeddingComparisonResponse)
async def compare_embedding_models(request: EmbeddingComparisonRequest):
    """
    Compare sentence-transformer and BERTurk embeddings for the same input text.
    """

    sentence_transformer_embedding = generate_embedding(request.text)
    berturk_embedding = generate_berturk_embedding(request.text)

    return EmbeddingComparisonResponse(
        input_preview=create_text_preview(request.text),
        sentence_transformer=EmbeddingModelPreview(
            model_name=EMBEDDING_MODEL_NAME,
            model_type="sentence-transformer",
            embedding_dimension=len(sentence_transformer_embedding),
            embedding_preview=sentence_transformer_embedding[:10],
        ),
        berturk=EmbeddingModelPreview(
            model_name=BERTURK_MODEL_NAME,
            model_type="berturk-transformer-encoder",
            embedding_dimension=len(berturk_embedding),
            embedding_preview=berturk_embedding[:10],
        ),
        explanation=(
            "The sentence-transformer model is currently used in the main matching "
            "pipeline because it is optimized for semantic similarity. BERTurk is "
            "included as an experimental Turkish transformer encoder for representation "
            "comparison and future AI improvements."
        ),
    )

@router.post("/ai/matching-evaluation", response_model=AIMatchingEvaluationResponse)
async def evaluate_ai_matching(request: AIMatchingEvaluationRequest):
    """
    Evaluate CV-job matching with AI/NLP scoring details.
    """

    cv_embedding = generate_embedding(request.cv_text)
    job_embedding = generate_embedding(request.job_text)

    similarity_score = calculate_cosine_similarity(
        first_embedding=cv_embedding,
        second_embedding=job_embedding,
    )

    semantic_score = round(similarity_score * 100, 2)

    cv_entities = extract_entities(request.cv_text)
    job_entities = extract_entities(request.job_text)

    skill_score = _calculate_skill_score_for_ai(
        cv_skills=cv_entities.skills,
        job_skills=job_entities.skills,
    )

    experience_score = 100.0

    if (
        request.candidate_years_experience is not None
        and request.required_years_experience is not None
    ):
        if request.candidate_years_experience >= request.required_years_experience:
            experience_score = 100.0
        else:
            experience_score = round(
                (request.candidate_years_experience / request.required_years_experience)
                * 100,
                2,
            )

    final_score = calculate_final_score(
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
    )

    score_breakdown = _build_score_breakdown(
    semantic_score=semantic_score,
    skill_score=skill_score,
    experience_score=experience_score,
)

    matched_skills = sorted(
        set(cv_entities.skills).intersection(set(job_entities.skills))
    )

    missing_skills = sorted(
    set(job_entities.skills) - set(cv_entities.skills)
)

    recommendation_level = _get_recommendation_level_for_ai(final_score)

    strengths = _build_ai_strengths(
        matched_skills=matched_skills,
        semantic_score=semantic_score,
        experience_score=experience_score,
    )

    weaknesses = _build_ai_weaknesses(
        matched_skills=matched_skills,
        job_skill_count=len(job_entities.skills),
        semantic_score=semantic_score,
        experience_score=experience_score,
    )

    ai_comment = _build_ai_comment(
        final_score=final_score,
        recommendation_level=recommendation_level,
    )

    confidence_level = _get_confidence_level_for_ai(
    semantic_score=semantic_score,
    skill_score=skill_score,
    experience_score=experience_score,
    job_skill_count=len(job_entities.skills),
    )

    risk_flags = _build_risk_flags_for_ai(
    semantic_score=semantic_score,
    skill_score=skill_score,
    experience_score=experience_score,
    missing_skills=missing_skills,
)

    return AIMatchingEvaluationResponse(
    semantic_score=semantic_score,
    skill_score=skill_score,
    experience_score=experience_score,
    final_score=final_score,
    score_breakdown=score_breakdown,
    recommendation_level=recommendation_level,
    confidence_level=confidence_level,
    risk_flags=risk_flags,
    matched_skills=matched_skills,
    missing_skills=missing_skills,
    cv_entities=cv_entities,
    job_entities=job_entities,
    strengths=strengths,
    weaknesses=weaknesses,
    ai_comment=ai_comment,
)