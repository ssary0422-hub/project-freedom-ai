from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError


BASE_DIR = Path(__file__).resolve().parent.parent
MATERIAL_DIR = BASE_DIR / "static" / "generated" / "materials"
MATERIAL_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
# Current phone cameras regularly produce 7–15 MB originals. The browser
# normally downsizes them first, but this larger server-side ceiling prevents a
# valid mobile upload from being silently discarded when that step is skipped.
MAX_BYTES = 16 * 1024 * 1024
MAX_PIXELS = 40_000_000


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
            if source.width * source.height > MAX_PIXELS:
                return ""
            # Phone cameras commonly store portrait orientation in EXIF instead
            # of rotating the pixel data. Apply it before converting to PNG,
            # because conversion discards that metadata.
            image = ImageOps.exif_transpose(source).convert("RGBA")
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
