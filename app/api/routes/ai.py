from fastapi import APIRouter

from app.schemas.ai import AIModelInfo, AIModelsResponse
from app.services.embedding import EMBEDDING_MODEL_NAME

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
            "NER fallback, and explainable ranking based on semantic similarity, "
            "skill overlap, and experience compatibility."
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
                name="BERTurk or Turkish Transformer NER",
                type="Transformer token classification model",
                purpose=(
                    "Planned transformer-based NER layer for extracting entities "
                    "such as skills, job titles, companies, dates, and education "
                    "from Turkish CVs and job postings."
                ),
                status="Planned",
            ),
        ],
        planned_improvements=[
            "Integrate a Turkish transformer-based NER model.",
            "Merge transformer NER outputs with rule-based domain extraction.",
            "Add confidence/source information for extracted entities.",
            "Persist embeddings in PostgreSQL with pgvector.",
            "Use vector similarity search for scalable retrieval.",
        ],
    )