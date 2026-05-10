import math
from typing import Any

from app.core.config import get_settings

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None


_embedding_model: Any = None


def generate_embedding(text: str) -> list[float]:
    settings = get_settings()
    model = _get_model()

    if settings.embedding_fallback_only or model is None:
        return _deterministic_embedding(text, settings.embedding_dimension)

    try:
        vector = model.encode(text, normalize_embeddings=True)
        if hasattr(vector, "tolist"):
            vector = vector.tolist()
        return _resize_vector(list(vector), settings.embedding_dimension)
    except Exception:
        return _deterministic_embedding(text, settings.embedding_dimension)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    return [generate_embedding(text) for text in texts]


def _get_model() -> Any:
    global _embedding_model
    settings = get_settings()

    if settings.embedding_fallback_only or SentenceTransformer is None:
        return None

    if _embedding_model is None:
        try:
            _embedding_model = SentenceTransformer(settings.embedding_model_name)
        except Exception:
            return None

    return _embedding_model


def _resize_vector(vector: list[float], dimension: int) -> list[float]:
    if len(vector) < dimension:
        vector = vector + [0.0] * (dimension - len(vector))
    elif len(vector) > dimension:
        vector = vector[:dimension]

    norm = math.sqrt(sum(value * value for value in vector))
    if norm > 0:
        vector = [value / norm for value in vector]

    return vector


def _deterministic_embedding(text: str, dimension: int) -> list[float]:
    seed = 0
    for byte in text.encode("utf-8", errors="ignore"):
        seed = (seed * 131 + byte) % (2**31)

    state = seed or 1
    vector: list[float] = []
    for _ in range(dimension):
        state = (1103515245 * state + 12345) % (2**31)
        vector.append((state / (2**30)) - 1.0)

    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector
