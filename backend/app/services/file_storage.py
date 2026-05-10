from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings


def save_pdf_bytes(filename: str, payload: bytes) -> Path:
    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = filename.replace(" ", "_")
    output_path = upload_dir / f"{uuid4().hex}_{safe_name}"
    output_path.write_bytes(payload)
    return output_path
