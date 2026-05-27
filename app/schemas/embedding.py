from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """
    Request schema for generating a text embedding.
    """

    text: str = Field(..., min_length=20)


class EmbeddingResponse(BaseModel):
    """
    Response schema for embedding generation preview.
    """

    model_name: str
    dimension: int
    vector_preview: list[float]