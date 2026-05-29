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
    AIEvaluationMetadata,
    AIDemoTestCase,
    AIDemoTestCasesResponse,
    NEREvaluationDatasetResponse,
    NEREvaluationExpectedEntities,
    NEREvaluationTestCase,
    NEREvaluationCaseResult,
    NEREvaluationMetricsResponse,
)
from app.services.embedding import EMBEDDING_MODEL_NAME, generate_embedding
from app.services.transformer_ner import (
    TURKISH_NER_MODEL_NAME,
    extract_transformer_ner_entities,
)
from app.services.hybrid_ner import extract_hybrid_entities
from app.services.ner import extract_entities, normalize_skill_name
from app.services.ingestion import create_text_preview
from app.services.berturk_embedding import (
    BERTURK_MODEL_NAME,
    generate_berturk_embedding,
)
from app.services.ranking import calculate_final_score
from app.services.similarity import calculate_cosine_similarity


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
    missing_critical_skills: list[str],
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

    if missing_critical_skills:
        risk_flags.append("MISSING_CRITICAL_SKILLS")

    elif len(missing_skills) >= 3:
        risk_flags.append("MANY_MISSING_REQUIRED_SKILLS")

    if not risk_flags:
        risk_flags.append("NO_MAJOR_RISK_DETECTED")

    return risk_flags


def _build_ai_evaluation_metadata() -> AIEvaluationMetadata:
    """
    Build metadata describing the AI evaluation methodology.
    """

    return AIEvaluationMetadata(
        evaluation_method="hybrid_semantic_and_structural_cv_job_matching",
        semantic_model=EMBEDDING_MODEL_NAME,
        entity_extraction_method="rule_based_entity_extraction_with_normalization",
        ranking_strategy=(
            "weighted_scoring_with_semantic_similarity_skill_overlap_and_experience"
        ),
        explainability_features=[
            "score_breakdown",
            "matched_skills",
            "missing_skills",
            "missing_critical_skills",
            "entity_breakdown",
            "strengths",
            "weaknesses",
            "confidence_level",
            "risk_flags",
        ],
    )

def _entities_to_dict(entities) -> dict[str, list[str]]:
    """
    Convert entity object into a dictionary for evaluation.
    """

    return {
        "skills": entities.skills,
        "roles": entities.roles,
        "companies": entities.companies,
        "dates": entities.dates,
        "education": entities.education,
    }


def _normalize_entity_set(values: list[str]) -> set[str]:
    """
    Normalize entity values for fair comparison.
    """

    return set(value.strip().lower() for value in values if value.strip())


def _calculate_f1_score(precision: float, recall: float) -> float:
    """
    Calculate F1-score from precision and recall.
    """

    if precision + recall == 0:
        return 0.0

    return round(
        2 * ((precision * recall) / (precision + recall)),
        2,
    )


def _evaluate_entities(
    expected_entities: dict[str, list[str]],
    predicted_entities: dict[str, list[str]],
) -> dict:
    """
    Compare expected and predicted entities by category.
    """

    total_expected = 0
    total_predicted = 0
    total_correct = 0
    missed_entities = {}
    extra_entities = {}

    for category in ["skills", "roles", "companies", "dates", "education"]:
        expected_set = _normalize_entity_set(expected_entities.get(category, []))
        predicted_set = _normalize_entity_set(predicted_entities.get(category, []))

        correct_set = expected_set.intersection(predicted_set)

        total_expected += len(expected_set)
        total_predicted += len(predicted_set)
        total_correct += len(correct_set)

        missed_entities[category] = sorted(expected_set - predicted_set)
        extra_entities[category] = sorted(predicted_set - expected_set)

    precision = 0.0
    recall = 0.0

    if total_predicted > 0:
        precision = round((total_correct / total_predicted) * 100, 2)

    if total_expected > 0:
        recall = round((total_correct / total_expected) * 100, 2)

    f1_score = _calculate_f1_score(
        precision=precision,
        recall=recall,
    )

    return {
        "total_expected": total_expected,
        "total_predicted": total_predicted,
        "total_correct": total_correct,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "missed_entities": missed_entities,
        "extra_entities": extra_entities,
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

    normalized_critical_skills = sorted(
        set(
            normalize_skill_name(skill)
            for skill in request.critical_skills
            if skill.strip()
        )
    )

    missing_critical_skills = sorted(
        set(normalized_critical_skills) - set(cv_entities.skills)
    )

    recommendation_level = _get_recommendation_level_for_ai(final_score)

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
        missing_critical_skills=missing_critical_skills,
    )

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

    evaluation_metadata = _build_ai_evaluation_metadata()

    return AIMatchingEvaluationResponse(
        semantic_score=semantic_score,
        skill_score=skill_score,
        experience_score=experience_score,
        final_score=final_score,
        score_breakdown=score_breakdown,
        recommendation_level=recommendation_level,
        confidence_level=confidence_level,
        risk_flags=risk_flags,
        evaluation_metadata=evaluation_metadata,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        missing_critical_skills=missing_critical_skills,
        cv_entities=cv_entities,
        job_entities=job_entities,
        strengths=strengths,
        weaknesses=weaknesses,
        ai_comment=ai_comment,
    )


@router.get("/ai/demo-test-cases", response_model=AIDemoTestCasesResponse)
async def get_ai_demo_test_cases():
    """
    Return predefined AI matching demo test cases for project presentation.
    """

    return AIDemoTestCasesResponse(
        purpose=(
            "These predefined cases are designed for demonstrating the AI matching "
            "evaluation endpoint during project demo and jury presentation."
        ),
        test_cases=[
            AIDemoTestCase(
                case_id="strong_match_case",
                title="Strong Backend Developer Match",
                description=(
                    "The candidate has almost all required skills and enough experience."
                ),
                cv_text=(
                    "Aday İstanbul konumunda Backend Developer olarak 5 yıl çalışmıştır. "
                    "Python, FastAPI, PostgreSQL, Docker, Kubernetes, Redis ve REST API "
                    "teknolojilerinde deneyim sahibidir."
                ),
                job_text=(
                    "İstanbul lokasyonunda Backend Developer arıyoruz. Adayın Python, "
                    "FastAPI, PostgreSQL, Docker, Kubernetes, Redis ve REST API "
                    "deneyimine sahip olması beklenmektedir. En az 3 yıl deneyim gereklidir."
                ),
                candidate_years_experience=5,
                required_years_experience=3,
                critical_skills=[
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                    "Docker",
                    "Kubernetes",
                ],
                expected_result="STRONG_MATCH or GOOD_MATCH with HIGH confidence",
            ),
            AIDemoTestCase(
                case_id="partial_match_case",
                title="Partial Backend Developer Match",
                description=(
                    "The candidate has core backend skills but misses some advanced requirements."
                ),
                cv_text=(
                    "Aday Ankara konumunda Backend Developer olarak 3 yıl çalışmıştır. "
                    "Python, FastAPI, PostgreSQL ve Docker teknolojilerinde deneyim sahibidir."
                ),
                job_text=(
                    "Ankara lokasyonunda Senior Backend Developer arıyoruz. Adayın Python, "
                    "FastAPI, PostgreSQL, Docker, Kubernetes, Redis ve REST API "
                    "deneyimine sahip olması beklenmektedir. En az 5 yıl deneyim gereklidir."
                ),
                candidate_years_experience=3,
                required_years_experience=5,
                critical_skills=[
                    "Python",
                    "FastAPI",
                    "Kubernetes",
                    "Redis",
                ],
                expected_result="POSSIBLE_MATCH or GOOD_MATCH with risk flags",
            ),
            AIDemoTestCase(
                case_id="weak_match_case",
                title="Weak Match for Backend Role",
                description=(
                    "The candidate profile is from a different domain and lacks required backend skills."
                ),
                cv_text=(
                    "Aday satış ve müşteri ilişkileri alanında 1 yıl çalışmıştır. "
                    "Excel, raporlama ve müşteri iletişimi konularında deneyim sahibidir."
                ),
                job_text=(
                    "İstanbul lokasyonunda Senior Backend Developer arıyoruz. Adayın Python, "
                    "FastAPI, PostgreSQL, Docker, Kubernetes, Redis ve REST API "
                    "deneyimine sahip olması beklenmektedir. En az 5 yıl deneyim gereklidir."
                ),
                candidate_years_experience=1,
                required_years_experience=5,
                critical_skills=[
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                    "Docker",
                ],
                expected_result="WEAK_MATCH with LOW confidence and multiple risk flags",
            ),
        ],
    )

@router.get("/ai/ner-evaluation-dataset", response_model=NEREvaluationDatasetResponse)
async def get_ner_evaluation_dataset():
    """
    Return predefined NER evaluation test cases for project validation.
    """

    return NEREvaluationDatasetResponse(
        purpose=(
            "This dataset provides predefined Turkish CV and job text examples "
            "with expected entities for evaluating the NER component."
        ),
        evaluation_note=(
            "The next evaluation step will compare extracted entities against "
            "these expected entities and calculate precision, recall and F1-score."
        ),
        test_cases=[
            NEREvaluationTestCase(
                case_id="backend_cv_case",
                title="Backend Developer CV",
                text=(
                    "Aday İstanbul konumunda Backend Developer olarak 4 yıl çalışmıştır. "
                    "Python, FastAPI, PostgreSQL, Docker ve REST API teknolojilerinde "
                    "deneyim sahibidir. Bilgisayar Mühendisliği lisans mezunudur."
                ),
                expected_entities=NEREvaluationExpectedEntities(
                    skills=[
                        "Python",
                        "FastAPI",
                        "PostgreSQL",
                        "Docker",
                        "REST API",
                    ],
                    roles=[
                        "Backend Developer",
                    ],
                    companies=[],
                    dates=[
                        "4 yıl",
                    ],
                    education=[
                        "Bilgisayar Mühendisliği",
                    ],
                ),
            ),
            NEREvaluationTestCase(
                case_id="data_scientist_cv_case",
                title="Data Scientist CV",
                text=(
                    "Aday Data Scientist olarak 3 yıl görev almıştır. Python, "
                    "Machine Learning, Deep Learning, NLP ve SQL konularında "
                    "deneyimlidir. Yüksek Lisans eğitimini Veri Bilimi alanında tamamlamıştır."
                ),
                expected_entities=NEREvaluationExpectedEntities(
                    skills=[
                        "Python",
                        "Machine Learning",
                        "Deep Learning",
                        "NLP",
                        "SQL",
                    ],
                    roles=[
                        "Data Scientist",
                    ],
                    companies=[],
                    dates=[
                        "3 yıl",
                    ],
                    education=[
                        "Yüksek Lisans",
                        "Veri Bilimi",
                    ],
                ),
            ),
            NEREvaluationTestCase(
                case_id="frontend_job_case",
                title="Frontend Developer Job Posting",
                text=(
                    "React, JavaScript, TypeScript, HTML ve CSS bilen Frontend Developer "
                    "aranmaktadır. Adayın en az 2 yıl deneyimli olması beklenmektedir."
                ),
                expected_entities=NEREvaluationExpectedEntities(
                    skills=[
                        "React",
                        "JavaScript",
                        "TypeScript",
                        "HTML",
                        "CSS",
                    ],
                    roles=[
                        "Frontend Developer",
                    ],
                    companies=[],
                    dates=[
                        "en az 2 yıl",
                    ],
                    education=[],
                ),
            ),
            NEREvaluationTestCase(
                case_id="devops_job_case",
                title="DevOps Engineer Job Posting",
                text=(
                    "DevOps Engineer pozisyonu için Docker, Kubernetes, Linux, Git "
                    "ve PostgreSQL deneyimi olan adaylar aranmaktadır. Minimum 5 yıl "
                    "deneyim gereklidir."
                ),
                expected_entities=NEREvaluationExpectedEntities(
                    skills=[
                        "Docker",
                        "Kubernetes",
                        "Linux",
                        "Git",
                        "PostgreSQL",
                    ],
                    roles=[
                        "DevOps Engineer",
                    ],
                    companies=[],
                    dates=[
                        "Minimum 5 yıl",
                    ],
                    education=[],
                ),
            ),
        ],
    )

@router.post("/ai/ner-evaluate", response_model=NEREvaluationMetricsResponse)
async def evaluate_ner_performance():
    """
    Evaluate NER performance using the predefined NER evaluation dataset.
    """

    dataset = await get_ner_evaluation_dataset()

    case_results = []

    total_expected_entities = 0
    total_predicted_entities = 0
    total_correct_entities = 0

    for test_case in dataset.test_cases:
        predicted_entities = extract_entities(test_case.text)

        expected_entities_dict = {
            "skills": test_case.expected_entities.skills,
            "roles": test_case.expected_entities.roles,
            "companies": test_case.expected_entities.companies,
            "dates": test_case.expected_entities.dates,
            "education": test_case.expected_entities.education,
        }

        predicted_entities_dict = _entities_to_dict(predicted_entities)

        evaluation_result = _evaluate_entities(
            expected_entities=expected_entities_dict,
            predicted_entities=predicted_entities_dict,
        )

        total_expected_entities += evaluation_result["total_expected"]
        total_predicted_entities += evaluation_result["total_predicted"]
        total_correct_entities += evaluation_result["total_correct"]

        case_results.append(
            NEREvaluationCaseResult(
                case_id=test_case.case_id,
                title=test_case.title,
                expected_entity_count=evaluation_result["total_expected"],
                predicted_entity_count=evaluation_result["total_predicted"],
                correct_entity_count=evaluation_result["total_correct"],
                precision=evaluation_result["precision"],
                recall=evaluation_result["recall"],
                f1_score=evaluation_result["f1_score"],
                missed_entities=evaluation_result["missed_entities"],
                extra_entities=evaluation_result["extra_entities"],
            )
        )

    overall_precision = 0.0
    overall_recall = 0.0

    if total_predicted_entities > 0:
        overall_precision = round(
            (total_correct_entities / total_predicted_entities) * 100,
            2,
        )

    if total_expected_entities > 0:
        overall_recall = round(
            (total_correct_entities / total_expected_entities) * 100,
            2,
        )

    overall_f1_score = _calculate_f1_score(
        precision=overall_precision,
        recall=overall_recall,
    )

    return NEREvaluationMetricsResponse(
        evaluation_method="rule_based_ner_against_predefined_labeled_dataset",
        evaluated_case_count=len(dataset.test_cases),
        total_expected_entities=total_expected_entities,
        total_predicted_entities=total_predicted_entities,
        total_correct_entities=total_correct_entities,
        precision=overall_precision,
        recall=overall_recall,
        f1_score=overall_f1_score,
        case_results=case_results,
    )