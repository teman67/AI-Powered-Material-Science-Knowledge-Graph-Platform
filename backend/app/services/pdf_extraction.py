from pathlib import Path


def extract_text_from_pdf(file_path: Path) -> str:
    text = _extract_with_pymupdf(file_path)
    if text.strip():
        return text

    text = _extract_with_pdfplumber(file_path)
    if text.strip():
        return text

    raise ValueError("No extractable text was found in the uploaded PDF.")


def _extract_with_pymupdf(file_path: Path) -> str:
    try:
        import fitz

        chunks: list[str] = []
        with fitz.open(file_path) as document:
            for page in document:
                chunks.append(page.get_text("text"))
        return "\n".join(chunks)
    except Exception:
        return ""


def _extract_with_pdfplumber(file_path: Path) -> str:
    try:
        import pdfplumber

        chunks: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                chunks.append(page.extract_text() or "")
        return "\n".join(chunks)
    except Exception:
        return ""
