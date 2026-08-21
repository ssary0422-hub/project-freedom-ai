"""Shared campaign art direction for SNS, ads, blog covers, and posters.

The module deliberately separates creative planning from pixel rendering.  A
model may propose concepts, but only concepts that satisfy the media contract
and are meaningfully different are allowed through.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable


BASE_DIR = Path(__file__).resolve().parent.parent
HISTORY_PATH = BASE_DIR / "instance" / "campaign_art_history.json"

LAYOUT_FAMILIES = (
    "full_bleed_photo",
    "split_scene",
    "product_closeup",
    "bold_offer",
    "testimonial",
    "problem_solution",
    "photo_collage",
    "editorial_type",
    "location_first",
    "step_by_step",
)

MESSAGE_ANGLES = (
    "customer_problem",
    "customer_outcome",
    "service_proof",
    "offer_action",
    "local_convenience",
    "brand_story",
)

MEDIA_RULES = {
    "sns": {"aspect_ratio": "4:5", "required": ("hook", "engagement")},
    "ads": {"aspect_ratio": "4:5", "required": ("benefit", "cta")},
    "blog": {"aspect_ratio": "16:9", "required": ("search_intent", "trust")},
    "poster": {"aspect_ratio": "print", "required": ("distance_readability", "contact")},
}


@dataclass(frozen=True)
class ArtDirection:
    concept_name: str
    campaign_angle: str
    layout_family: str
    message_angle: str
    photo_strategy: str
    subject_position: str
    headline_position: str
    mood: str
    headline: str
    supporting_copy: str
    cta: str
    palette: tuple[str, str, str]
    avoid: tuple[str, ...]


def _read_history() -> dict[str, list[dict]]:
    try:
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _write_history(history: dict[str, list[dict]]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_PATH.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def _identity(company: str, business: str, media: str) -> str:
    return f"{media}:{(company or business or 'default').strip().casefold()}"


def recent_fingerprints(company: str, business: str, media: str, limit: int = 10) -> list[dict]:
    return _read_history().get(_identity(company, business, media), [])[-limit:]


def _extract_json(text: str):
    cleaned = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.S | re.I)
    if fenced:
        cleaned = fenced.group(1).strip()
    start_candidates = [index for index in (cleaned.find("["), cleaned.find("{")) if index >= 0]
    if start_candidates:
        cleaned = cleaned[min(start_candidates):]
    return json.loads(cleaned)


def _direction_from_dict(item: dict) -> ArtDirection:
    palette = tuple(item.get("palette") or ("#071827", "#59e1cb", "#f7fbff"))
    avoid = tuple(str(value) for value in item.get("avoid", ()))
    return ArtDirection(
        concept_name=str(item.get("concept_name", "")).strip(),
        campaign_angle=str(item.get("campaign_angle", "")).strip(),
        layout_family=str(item.get("layout_family", "")).strip(),
        message_angle=str(item.get("message_angle", "")).strip(),
        photo_strategy=str(item.get("photo_strategy", "")).strip(),
        subject_position=str(item.get("subject_position", "")).strip(),
        headline_position=str(item.get("headline_position", "")).strip(),
        mood=str(item.get("mood", "")).strip(),
        headline=str(item.get("headline", "")).strip(),
        supporting_copy=str(item.get("supporting_copy", "")).strip(),
        cta=str(item.get("cta", "")).strip(),
        palette=palette[:3],
        avoid=avoid,
    )


def direction_from_payload(item: dict) -> ArtDirection:
    """Validate one user-selected direction without trusting browser JSON."""
    if not isinstance(item, dict):
        raise ValueError("Art direction must be an object")
    direction = _direction_from_dict(item)
    if direction.layout_family not in LAYOUT_FAMILIES:
        raise ValueError(f"Unknown layout family: {direction.layout_family}")
    if direction.message_angle not in MESSAGE_ANGLES:
        raise ValueError(f"Unknown message angle: {direction.message_angle}")
    if not all((direction.concept_name, direction.campaign_angle, direction.headline, direction.cta)):
        raise ValueError("Selected direction is incomplete")
    if len(direction.palette) != 3:
        raise ValueError("Selected direction needs a three-color palette")
    return direction


def validate_directions(directions: list[ArtDirection], media: str) -> None:
    if media not in MEDIA_RULES:
        raise ValueError(f"Unsupported media: {media}")
    if len(directions) != 3:
        raise ValueError("Exactly three art directions are required")
    if len({item.layout_family for item in directions}) != 3:
        raise ValueError("The three concepts must use different layouts")
    if len({item.message_angle for item in directions}) != 3:
        raise ValueError("The three concepts must use different message angles")
    if len({item.photo_strategy for item in directions}) != 3:
        raise ValueError("The three concepts must use different photo strategies")
    for item in directions:
        if item.layout_family not in LAYOUT_FAMILIES:
            raise ValueError(f"Unknown layout family: {item.layout_family}")
        if item.message_angle not in MESSAGE_ANGLES:
            raise ValueError(f"Unknown message angle: {item.message_angle}")
        if not all((item.concept_name, item.campaign_angle, item.headline, item.cta)):
            raise ValueError("Every concept needs a name, angle, headline, and CTA")
        if len(item.palette) != 3:
            raise ValueError("Every concept needs a three-color palette")


def _prompt(*, business: str, company: str, request: str, media: str,
            photo_count: int, recent: list[dict]) -> str:
    rules = MEDIA_RULES[media]
    return f"""
You are the senior art director for Project Freedom AI.
Create exactly three genuinely different {media} campaign concepts as a JSON array.

Business: {business}
Brand: {company}
Verified user request: {request}
Uploaded real photo count: {photo_count}
Output ratio: {rules['aspect_ratio']}
Media priorities: {', '.join(rules['required'])}
Recent designs that must not be repeated: {json.dumps(recent, ensure_ascii=False)}

Hard rules:
- Never invent a price, address, result, review, credential, date, or contact method.
- The three concepts must have different layout_family, message_angle, and photo_strategy values.
- Choose layout_family only from: {', '.join(LAYOUT_FAMILIES)}.
- Choose message_angle only from: {', '.join(MESSAGE_ANGLES)}.
- Use uploaded photos prominently when they exist; do not pretend an AI scene is the real store.
- Keep Korean headlines concise and immediately understandable.
- Avoid the repeated combination of navy background, top-right circle, middle information card, and bottom pill CTA.

Each object must contain exactly these fields:
concept_name, campaign_angle, layout_family, message_angle, photo_strategy,
subject_position, headline_position, mood, headline, supporting_copy, cta,
palette (three hex colors), avoid (array of visual repetitions).
Return JSON only.
""".strip()


def create_art_directions(*, business: str, company: str, request: str, media: str,
                          photo_count: int = 0, generator: Callable[[str], str],
                          remember: bool = True) -> list[ArtDirection]:
    if media not in MEDIA_RULES:
        raise ValueError(f"Unsupported media: {media}")
    recent = recent_fingerprints(company, business, media)
    payload = _extract_json(generator(_prompt(
        business=business,
        company=company,
        request=request,
        media=media,
        photo_count=photo_count,
        recent=recent,
    )))
    if isinstance(payload, dict):
        payload = payload.get("concepts", [])
    directions = [_direction_from_dict(item) for item in payload]
    validate_directions(directions, media)

    recent_layouts = {item.get("layout_family") for item in recent[-3:]}
    if recent_layouts and all(item.layout_family in recent_layouts for item in directions):
        raise ValueError("All proposed layouts repeat the most recent campaign designs")

    if remember:
        history = _read_history()
        key = _identity(company, business, media)
        entries = history.setdefault(key, [])
        entries.extend({
            "layout_family": item.layout_family,
            "message_angle": item.message_angle,
            "photo_strategy": item.photo_strategy,
            "headline_position": item.headline_position,
            "subject_position": item.subject_position,
        } for item in directions)
        history[key] = entries[-30:]
        _write_history(history)
    return directions


def serialize_directions(directions: list[ArtDirection]) -> list[dict]:
    return [asdict(item) for item in directions]
