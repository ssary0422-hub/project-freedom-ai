import base64
import os
from functools import lru_cache
from typing import Any

import requests


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
DEFAULT_CLOUDFLARE_IMAGE_MODEL = "@cf/black-forest-labs/flux-1-schnell"


def _post_json(url: str, *, headers: dict[str, str] | None = None,
               payload: dict[str, Any], timeout: int) -> requests.Response:
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if not response.ok:
        # Keep provider diagnostics useful without ever logging credentials.
        detail = response.text[:500].replace("\n", " ")
        raise RuntimeError(
            f"AI provider returned HTTP {response.status_code}: {detail}"
        )
    return response


@lru_cache(maxsize=4)
def _available_gemini_models(api_key: str) -> tuple[str, ...]:
    """Return text-capable models actually enabled for this API key."""
    response = requests.get(
        "https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key": api_key},
        timeout=30,
    )
    if not response.ok:
        detail = response.text[:500].replace("\n", " ")
        raise RuntimeError(
            f"Gemini model discovery returned HTTP {response.status_code}: {detail}"
        )
    models = []
    for item in response.json().get("models", []):
        methods = item.get("supportedGenerationMethods") or []
        name = str(item.get("name", "")).removeprefix("models/")
        if name and "generateContent" in methods and "gemini" in name:
            models.append(name)
    return tuple(models)


def _gemini_model_candidates(api_key: str) -> list[str]:
    configured = os.getenv("GEMINI_MODEL", "").strip()
    preferred = [
        configured,
        DEFAULT_GEMINI_MODEL,
        "gemini-2.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
    ]
    available = list(_available_gemini_models(api_key))
    ordered = [model for model in preferred if model and model in available]
    ordered.extend(
        model for model in available
        if model not in ordered and "flash" in model and "preview" not in model
    )
    ordered.extend(model for model in available if model not in ordered)
    if not ordered:
        raise RuntimeError("This Gemini API key has no generateContent model enabled.")
    return ordered


def generate_text(prompt: str) -> str:
    """Generate marketing copy with Gemini's free-tier API."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is required.")

    candidates_to_try = _gemini_model_candidates(api_key)
    response = None
    last_error = None
    for model in candidates_to_try:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        try:
            response = _post_json(
                url,
                headers={"x-goog-api-key": api_key},
                payload={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 8192},
                },
                timeout=120,
            )
            break
        except RuntimeError as exc:
            last_error = exc
    if response is None:
        raise RuntimeError(f"Every enabled Gemini model failed. Last error: {last_error}")
    data = response.json()
    candidates = data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini returned no text candidate.")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise RuntimeError("Gemini returned an empty text response.")
    return text


def provider_status() -> dict[str, bool | str]:
    """Expose configuration state without ever returning secret values."""
    return {
        "text_provider": "gemini",
        "text_ready": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        "image_provider": "cloudflare-workers-ai",
        "image_ready": bool(
            os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
            and os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
        ),
        "paid_fallback": False,
    }


def generate_image_bytes(prompt: str) -> bytes:
    """Generate an image with Cloudflare Workers AI's daily free allocation."""
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    api_token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    if not account_id or not api_token:
        raise RuntimeError(
            "CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN are required."
        )

    model = os.getenv(
        "CLOUDFLARE_IMAGE_MODEL", DEFAULT_CLOUDFLARE_IMAGE_MODEL
    ).strip()
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
    response = _post_json(
        url,
        headers={"Authorization": f"Bearer {api_token}"},
        payload={"prompt": prompt, "num_steps": 4},
        timeout=180,
    )

    content_type = response.headers.get("content-type", "").lower()
    if content_type.startswith("image/"):
        return response.content

    data = response.json()
    if not data.get("success", True):
        raise RuntimeError(f"Cloudflare image generation failed: {data.get('errors')}")

    result = data.get("result") or {}
    encoded = result.get("image") if isinstance(result, dict) else None
    if not encoded and isinstance(result, str):
        encoded = result
    if not encoded:
        raise RuntimeError("Cloudflare returned no image data.")
    return base64.b64decode(encoded)
