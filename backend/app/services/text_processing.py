import re


def clean_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n")
    text = re.sub(r"-\n", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_title_from_text(text: str) -> str | None:
    for line in text.splitlines():
        candidate = line.strip()
        if 8 <= len(candidate) <= 200:
            return candidate
    return None


def split_text_into_chunks(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []

    effective_overlap = max(0, min(chunk_overlap, chunk_size - 1))
    step = max(1, chunk_size - effective_overlap)

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        if not chunk_words:
            break
        chunks.append(" ".join(chunk_words))
        if end == len(words):
            break
        start += step

    return chunks
