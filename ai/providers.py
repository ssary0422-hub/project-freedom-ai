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
    # ``generate_text`` receives the complete prompt; there is no separate
    # ``goal`` argument here.  Keep this local fallback defined because older
    # prompt-length compatibility branches below still reference it.
    goal = ""
    if "long" in prompt:
        goal = f"{goal}; 사용자가 원하는 말할 문장은 3~4문장으로 조금 더 자세하고 충분하게 작성한다."
    elif "short" in prompt:
        goal = f"{goal}; 사용자가 원하는 말할 문장은 한 문장으로 아주 짧게 작성한다."
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


def generate_speaking_coach_json(
    *, person: str, situation: str, message: str, goal: str, tone: str,
    quick: bool = False,
) -> dict:
    """Generate practical Korean speaking-coach lines as structured JSON."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required.")

    model = os.getenv("OPENAI_TEXT_MODEL", DEFAULT_OPENAI_TEXT_MODEL).strip()
    mode = "핵심 한 문장만 아주 짧게" if quick else "바로 말할 문장과 변형 2개"
    prompt = f"""
너는 '순금이 말하기 코치'다. 사용자가 실제 현장에서 바로 말할 수 있는 자연스러운 한국어를 만든다.
상대: {person}
상황: {situation}
사용자가 적은 내용: {message}
꼭 전하고 싶은 말: {goal}
원하는 말투: {tone}
출력 모드: {mode}

지침:
- 특정 사용자의 이름을 부르지 않고, 누구에게나 자연스럽고 따뜻한 코치 톤을 유지한다.
- 훈계하거나 상대를 공격하는 표현은 피한다.
- 입력에 없는 사실을 만들어내지 않는다.
- quick 모드에서는 sentence 하나만 1~2문장으로 짧게 만든다.
""".strip()
    try:
        response = OpenAI(api_key=api_key).responses.create(
            model=model or DEFAULT_OPENAI_TEXT_MODEL,
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "speaking_coach_lines",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "sentence": {"type": "string"},
                            "soft": {"type": "string"},
                            "firm": {"type": "string"},
                            "coach_note": {"type": "string"},
                        },
                        "required": ["sentence", "soft", "firm", "coach_note"],
                        "additionalProperties": False,
                    },
                }
            },
            max_output_tokens=700 if quick else 1100,
        )
    except Exception as exc:
        raise RuntimeError(f"OpenAI speaking coach generation failed: {exc}") from exc
    try:
        result = json.loads(response.output_text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("OpenAI returned invalid speaking coach JSON.") from exc
    if not all(isinstance(result.get(key), str) and result[key].strip() for key in ("sentence", "soft", "firm", "coach_note")):
        raise RuntimeError("OpenAI returned incomplete speaking coach JSON.")
    return result


def generate_running_coach_json(*, condition: str, minutes: int, goal: str) -> dict:
    """Generate one structured, personalized no-video running plan."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required.")
    model = os.getenv("OPENAI_TEXT_MODEL", DEFAULT_OPENAI_TEXT_MODEL).strip()
    prompt = f"""
너는 순금이라는 이름의 순둥순둥한 러닝 코치야.
사용자 컨디션: {condition}
오늘 가능한 시간(분): {minutes}
러닝 목표: {goal}

위 정보를 바탕으로 오늘 바로 실행할 수 있는 안전한 러닝 안내를 한국어로 작성해.
거리보다 시간과 체감 강도를 우선하고, 통증이 있으면 달리기를 중단하도록 안내해.
답변은 반드시 아래 JSON 구조만 사용해.
""".strip()
    response = OpenAI(api_key=api_key).responses.create(
        model=model or DEFAULT_OPENAI_TEXT_MODEL,
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "running_coach_plan",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "plan": {"type": "string"},
                        "intensity": {"type": "string"},
                        "warmup": {"type": "string"},
                        "caution": {"type": "string"},
                        "cooldown": {"type": "string"},
                        "cheer": {"type": "string"},
                    },
                    "required": ["title", "plan", "intensity", "warmup", "caution", "cooldown", "cheer"],
                    "additionalProperties": False,
                },
            }
        },
        max_output_tokens=900,
    )
    try:
        result = json.loads(response.output_text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("OpenAI returned invalid running coach JSON.") from exc
    required = ("title", "plan", "intensity", "warmup", "caution", "cooldown", "cheer")
    if not all(isinstance(result.get(key), str) and result[key].strip() for key in required):
        raise RuntimeError("OpenAI returned incomplete running coach JSON.")
    return result


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
    # Older deployments may still have the invalid ``gpt-image-2`` value in
    # their environment. Normalize it in code so a stale setting cannot break
    # every paid image request after deployment.
    if model == "gpt-image-2":
        model = DEFAULT_OPENAI_IMAGE_MODEL
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
