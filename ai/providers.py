import base64
import json
import mimetypes
import os
from pathlib import Path
from openai import OpenAI


DEFAULT_OPENAI_TEXT_MODEL = "gpt-5.4"
# GPT Image 1 is the stable Images API model.  ``gpt-image-2`` is not a
# supported Images API model and causes every paid image request to fail.
DEFAULT_OPENAI_IMAGE_MODEL = "gpt-image-1"
DEFAULT_OPENAI_IMAGE_QUALITY = "medium"


def generate_text(prompt: str) -> str:
    """Generate premium marketing copy with OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required.")
    model = os.getenv("OPENAI_TEXT_MODEL", DEFAULT_OPENAI_TEXT_MODEL).strip()
    try:
        response = OpenAI(api_key=api_key).responses.create(
            model=model or DEFAULT_OPENAI_TEXT_MODEL,
            input=prompt,
            max_output_tokens=8192,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI text generation failed: {exc}") from exc
    text = (response.output_text or "").strip()
    if not text:
        raise RuntimeError("OpenAI returned an empty text response.")
    return text


def analyze_images_json(prompt: str, image_paths: list[str | Path]) -> dict:
    """Inspect one or more finished visuals in a single metered QA request."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required.")
    paths = [Path(value) for value in image_paths]
    if not paths:
        raise ValueError("At least one image is required for visual QA.")
    model = os.getenv("OPENAI_TEXT_MODEL", DEFAULT_OPENAI_TEXT_MODEL).strip()
    try:
        response = OpenAI(api_key=api_key).responses.create(
            model=model or DEFAULT_OPENAI_TEXT_MODEL,
            input=[{
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}] + [
                    {
                        "type": "input_image",
                        "image_url": "data:{mime};base64,{encoded}".format(
                            mime=mimetypes.guess_type(path.name)[0] or "image/png",
                            encoded=base64.b64encode(path.read_bytes()).decode("ascii"),
                        ),
                    }
                    for path in paths
                ],
            }],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "campaign_visual_quality",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "integer", "minimum": 0, "maximum": 100},
                            "approved": {"type": "boolean"},
                            "issues": {"type": "array", "items": {"type": "string"}},
                            "blockers": {"type": "array", "items": {"type": "string"}},
                            "strengths": {"type": "array", "items": {"type": "string"}},
                            "retry_instruction": {"type": "string"},
                        },
                        "required": ["score", "approved", "issues", "blockers", "strengths", "retry_instruction"],
                        "additionalProperties": False,
                    },
                }
            },
            max_output_tokens=1200,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI image analysis failed: {exc}") from exc
    try:
        return json.loads(response.output_text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("OpenAI returned invalid visual QA JSON.") from exc


def analyze_image_json(prompt: str, image_path: str | Path) -> dict:
    """Backward-compatible single-image visual QA helper."""
    return analyze_images_json(prompt, [image_path])


def provider_status() -> dict[str, bool | str]:
    """Expose configuration state without ever returning secret values."""
    return {
        "text_provider": "openai",
        "text_ready": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "image_provider": "openai",
        "image_ready": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "paid_fallback": False,
    }


def generate_image_bytes(prompt: str) -> bytes:
    """Generate a consistently high-quality image with OpenAI."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required.")

    model = os.getenv("OPENAI_IMAGE_MODEL", DEFAULT_OPENAI_IMAGE_MODEL).strip()
    quality = os.getenv(
        "OPENAI_IMAGE_QUALITY", DEFAULT_OPENAI_IMAGE_QUALITY
    ).strip().lower()
    if quality not in {"low", "medium", "high", "auto"}:
        quality = DEFAULT_OPENAI_IMAGE_QUALITY

    try:
        result = OpenAI(api_key=api_key).images.generate(
            model=model or DEFAULT_OPENAI_IMAGE_MODEL,
            prompt=prompt,
            size="1024x1024",
            quality=quality,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI image generation failed: {exc}") from exc

    encoded = result.data[0].b64_json if result.data else None
    if not encoded:
        raise RuntimeError("OpenAI returned no image data.")
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("OpenAI returned invalid base64 image data.") from exc
    if not image_bytes.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n")):
        raise RuntimeError("OpenAI returned an unsupported image format.")
    return image_bytes
