import base64
import re
import uuid
from pathlib import Path

from app.config import settings

_DATA_URL_RE = re.compile(r"^data:(?P<mime>[\w/+.-]+);base64,(?P<data>.+)$", re.DOTALL)

_EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
}


def save_bytes(content: bytes, extension: str) -> str:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4()}{extension}"
    (upload_dir / stored_name).write_bytes(content)
    return f"/uploads/{stored_name}"


def save_data_url(data_url: str) -> str | None:
    """Decode a base64 data: URL (as produced by the browser's FileReader) to a stored file path."""
    match = _DATA_URL_RE.match(data_url)
    if not match:
        return None
    extension = _EXT_BY_MIME.get(match.group("mime"), ".jpg")
    content = base64.b64decode(match.group("data"))
    return save_bytes(content, extension)
