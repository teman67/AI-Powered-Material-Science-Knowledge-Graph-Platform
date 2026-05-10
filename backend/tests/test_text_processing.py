from app.services.text_processing import clean_text, split_text_into_chunks


def test_clean_text_merges_hyphenated_line_break() -> None:
    raw = "Thermo-\nconductive materials\n\n\nare useful."
    cleaned = clean_text(raw)

    assert "Thermoconductive" in cleaned
    assert "\n\n\n" not in cleaned


def test_split_text_into_chunks_with_overlap() -> None:
    text = " ".join(f"w{i}" for i in range(20))
    chunks = split_text_into_chunks(text, chunk_size=8, chunk_overlap=2)

    assert len(chunks) == 3
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]
