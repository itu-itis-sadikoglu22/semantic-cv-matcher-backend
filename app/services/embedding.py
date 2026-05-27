from functools import lru_cache

from sentence_transformers import SentenceTransformer


EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Load and cache the sentence embedding model.

    The model is multilingual and suitable for Turkish semantic similarity tasks.
    """

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def generate_embedding(text: str) -> list[float]:
    """
    Generate a dense vector embedding for a given text.
    """

    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)

    return embedding.tolist()