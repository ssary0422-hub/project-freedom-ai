from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError


BASE_DIR = Path(__file__).resolve().parent.parent
MATERIAL_DIR = BASE_DIR / "static" / "generated" / "materials"
MATERIAL_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 6 * 1024 * 1024


def save_uploaded_image(file_storage, prefix="material"):
    if not file_storage or file_storage.mimetype not in ALLOWED_MIME:
        return ""
    raw = file_storage.read(MAX_BYTES + 1)
    if not raw or len(raw) > MAX_BYTES:
        return ""
    from io import BytesIO

    try:
        with Image.open(BytesIO(raw)) as source:
            source.verify()
        with Image.open(BytesIO(raw)) as source:
            image = source.convert("RGBA")
            image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
            path = MATERIAL_DIR / f"{prefix}-{uuid4().hex[:12]}.png"
            image.save(path, "PNG", optimize=True)
            return str(path)
    except (UnidentifiedImageError, OSError, ValueError):
        return ""


def first_valid_uploaded_image(files, prefix="photo"):
    for file_storage in list(files)[:10]:
        saved = save_uploaded_image(file_storage, prefix)
        if saved:
            return saved
    return ""
