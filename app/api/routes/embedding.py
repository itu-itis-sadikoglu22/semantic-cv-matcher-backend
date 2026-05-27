from fastapi import APIRouter

from app.schemas.embedding import EmbeddingRequest, EmbeddingResponse
from app.services.embedding import EMBEDDING_MODEL_NAME, generate_embedding

router = APIRouter()


@router.post("/embeddings/generate", response_model=EmbeddingResponse)
async def generate_text_embedding(request: EmbeddingRequest):
    """
    Generate a dense embedding vector for a given text.
    """

    embedding = generate_embedding(request.text)

    return EmbeddingResponse(
        model_name=EMBEDDING_MODEL_NAME,
        dimension=len(embedding),
        vector_preview=embedding[:5],
    )