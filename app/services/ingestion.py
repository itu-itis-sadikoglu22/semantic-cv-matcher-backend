import re


def normalize_text(text: str) -> str:
    """
    Normalize raw CV or job posting text for downstream NLP processing.
    """

    # Replace multiple whitespace characters with a single space
    cleaned_text = re.sub(r"\s+", " ", text)

    # Remove leading and trailing spaces
    cleaned_text = cleaned_text.strip()

    return cleaned_text


def create_text_preview(text: str, max_length: int = 250) -> str:
    """
    Create a short preview from a longer raw text field.
    """

    normalized_text = normalize_text(text)

    if len(normalized_text) <= max_length:
        return normalized_text

    return normalized_text[:max_length].rstrip() + "..."