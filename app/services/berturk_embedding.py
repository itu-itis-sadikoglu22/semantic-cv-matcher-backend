from functools import lru_cache

import torch
from transformers import AutoModel, AutoTokenizer


BERTURK_MODEL_NAME = "dbmdz/bert-base-turkish-cased"


@lru_cache(maxsize=1)
def get_berturk_model_and_tokenizer():
    """
    Load and cache the BERTurk tokenizer and model.
    """

    tokenizer = AutoTokenizer.from_pretrained(BERTURK_MODEL_NAME)
    model = AutoModel.from_pretrained(BERTURK_MODEL_NAME)
    model.eval()

    return tokenizer, model


def generate_berturk_embedding(text: str) -> list[float]:
    """
    Generate a sentence-level embedding using mean pooling over BERTurk token embeddings.
    """

    tokenizer, model = get_berturk_model_and_tokenizer()

    encoded_input = tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt",
    )

    with torch.no_grad():
        model_output = model(**encoded_input)

    token_embeddings = model_output.last_hidden_state
    attention_mask = encoded_input["attention_mask"]

    input_mask_expanded = (
        attention_mask
        .unsqueeze(-1)
        .expand(token_embeddings.size())
        .float()
    )

    pooled_embedding = torch.sum(
        token_embeddings * input_mask_expanded,
        dim=1,
    ) / torch.clamp(
        input_mask_expanded.sum(dim=1),
        min=1e-9,
    )

    embedding = pooled_embedding[0].tolist()

    return [round(value, 6) for value in embedding]