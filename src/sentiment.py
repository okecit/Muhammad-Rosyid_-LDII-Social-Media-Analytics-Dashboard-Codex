from __future__ import annotations

import re
from functools import lru_cache

import pandas as pd


DEFAULT_HF_MODEL = "w11wo/indonesian-roberta-base-sentiment-classifier"

POSITIVE_TERMS = {
    "aamiin",
    "amin",
    "bagus",
    "baik",
    "bangga",
    "benar",
    "berkah",
    "hebat",
    "keren",
    "mantap",
    "masyaallah",
    "setuju",
    "suka",
    "salut",
    "terima kasih",
}

NEGATIVE_TERMS = {
    "aneh",
    "buruk",
    "benci",
    "bohong",
    "fitnah",
    "jangan",
    "jelek",
    "kafir",
    "keliru",
    "sesat",
    "takut",
    "tidak benar",
    "tolak",
}


def normalize_label(label: str) -> str:
    label = str(label).strip().lower()
    mapping = {
        "positive": "positif",
        "pos": "positif",
        "label_2": "positif",
        "neutral": "netral",
        "neu": "netral",
        "label_1": "netral",
        "negative": "negatif",
        "neg": "negatif",
        "label_0": "negatif",
    }
    return mapping.get(label, label if label in {"positif", "netral", "negatif"} else "netral")


@lru_cache(maxsize=1)
def get_sentiment_pipeline(model_name: str = DEFAULT_HF_MODEL):
    from transformers import pipeline

    return pipeline("sentiment-analysis", model=model_name, tokenizer=model_name, truncation=True)


def rule_based_sentiment(text: str) -> tuple[str, float]:
    lowered = re.sub(r"\s+", " ", str(text).lower())
    positive_score = sum(1 for term in POSITIVE_TERMS if term in lowered)
    negative_score = sum(1 for term in NEGATIVE_TERMS if term in lowered)

    if positive_score > negative_score:
        return "positif", min(0.95, 0.55 + positive_score * 0.12)
    if negative_score > positive_score:
        return "negatif", min(0.95, 0.55 + negative_score * 0.12)
    return "netral", 0.5


def classify_comments(
    df: pd.DataFrame,
    text_column: str = "comment",
    model_name: str = DEFAULT_HF_MODEL,
    batch_size: int = 16,
    use_transformer: bool = True,
) -> pd.DataFrame:
    """Add sentiment labels to comments, with a lightweight fallback."""
    result = df.copy()

    if not use_transformer:
        scored = result[text_column].apply(rule_based_sentiment)
        result["sentiment"] = scored.apply(lambda item: item[0])
        result["sentiment_score"] = scored.apply(lambda item: item[1])
        result["sentiment_method"] = "kamus sederhana"
        return result

    try:
        pipe = get_sentiment_pipeline(model_name)
        texts = result[text_column].fillna("").astype(str).tolist()
        predictions = pipe(texts, batch_size=batch_size)
        result["sentiment"] = [normalize_label(item.get("label", "")) for item in predictions]
        result["sentiment_score"] = [float(item.get("score", 0)) for item in predictions]
        result["sentiment_method"] = f"transformer: {model_name}"
    except Exception as exc:
        scored = result[text_column].apply(rule_based_sentiment)
        result["sentiment"] = scored.apply(lambda item: item[0])
        result["sentiment_score"] = scored.apply(lambda item: item[1])
        result["sentiment_method"] = f"fallback kamus sederhana ({exc.__class__.__name__})"

    return result
