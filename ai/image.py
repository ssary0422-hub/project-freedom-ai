import gc
import os
import uuid
from datetime import datetime
from pathlib import Path

from ai.providers import generate_image_bytes


BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = BASE_DIR / "static" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def _is_render() -> bool:
    return bool(os.getenv("RENDER"))


def _cleanup_old_images(keep: int = 20) -> None:
    try:
        files = sorted(
            GENERATED_DIR.glob("image_*.*"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for old_file in files[keep:]:
            try:
                old_file.unlink()
            except OSError:
                pass
    except Exception as error:
        print("Image cleanup error:", error)


def make_image(prompt: str) -> str:
    """Generate an image through Cloudflare Workers AI and return its app path."""
    if not prompt.strip():
        raise ValueError("Please enter an image description.")

    image_bytes = generate_image_bytes(prompt)
    if not image_bytes:
        raise RuntimeError("The image provider returned no image data.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    extension = ".jpg" if image_bytes.startswith(b"\xff\xd8\xff") else ".png"
    filename = f"image_{timestamp}_{unique_id}{extension}"
    filepath = GENERATED_DIR / filename
    filepath.write_bytes(image_bytes)

    del image_bytes
    gc.collect()

    if _is_render():
        _cleanup_old_images(keep=20)

    return filepath.relative_to(BASE_DIR).as_posix()
