import unicodedata


def normalize_location(location: str | None) -> str | None:
    """
    Normalize location text for case-insensitive and Turkish-character-insensitive comparison.
    """

    if location is None:
        return None

    normalized = location.strip().lower()

    # Convert Turkish-specific characters to ASCII-friendly equivalents
    translation_table = str.maketrans({
        "ı": "i",
        "İ": "i",
        "ş": "s",
        "ğ": "g",
        "ü": "u",
        "ö": "o",
        "ç": "c",
    })

    normalized = normalized.translate(translation_table)

    # Remove remaining accents if any
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(
        character for character in normalized
        if not unicodedata.combining(character)
    )

    return normalized