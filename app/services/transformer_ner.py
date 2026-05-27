from functools import lru_cache

from transformers import pipeline


TURKISH_NER_MODEL_NAME = "savasy/bert-base-turkish-ner-cased"


@lru_cache(maxsize=1)
def get_transformer_ner_pipeline():
    """
    Load and cache the transformer-based Turkish NER pipeline.
    """

    return pipeline(
        task="ner",
        model=TURKISH_NER_MODEL_NAME,
        tokenizer=TURKISH_NER_MODEL_NAME,
        aggregation_strategy="simple",
    )


def extract_transformer_ner_entities(text: str) -> list[dict]:
    """
    Extract named entities using a transformer-based Turkish NER model.
    """

    ner_pipeline = get_transformer_ner_pipeline()
    raw_entities = ner_pipeline(text)

    entities = []

    for entity in raw_entities:
        entity_text = entity.get("word", "").strip()
        entity_label = entity.get("entity_group") or entity.get("entity", "UNKNOWN")
        entity_score = float(entity.get("score", 0.0))

        if not entity_text:
            continue

        entities.append(
            {
                "text": entity_text,
                "label": entity_label,
                "score": round(entity_score, 4),
            }
        )

    return entities