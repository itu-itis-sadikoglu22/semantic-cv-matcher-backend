import numpy as np


def calculate_cosine_similarity(
    first_embedding: list[float],
    second_embedding: list[float],
) -> float:
    """
    Calculate cosine similarity between two normalized embedding vectors.
    """

    first_vector = np.array(first_embedding)
    second_vector = np.array(second_embedding)

    similarity = np.dot(first_vector, second_vector) / (
        np.linalg.norm(first_vector) * np.linalg.norm(second_vector)
    )

    return float(similarity)


def calculate_percentage_score(similarity: float) -> float:
    """
    Convert cosine similarity into a percentage-like score.
    """

    normalized_score = (similarity + 1) / 2
    percentage_score = normalized_score * 100

    return round(percentage_score, 2)