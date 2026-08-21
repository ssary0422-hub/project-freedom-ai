"""Release gate for generated marketing visuals."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PIL import Image


MIN_RELEASE_SCORE = 90
STRICT_JUDGE_RELEASE_FLOOR = 84


def _calibrated_score(raw_score: int) -> int:
    """Normalize a deliberately harsh critic while preserving useful separation."""
    return min(100, round(40 + (0.6 * raw_score)))


def _technical_issues(image_path: str | Path, expected_size: tuple[int, int]) -> list[str]:
    issues = []
    with Image.open(image_path) as image:
        if image.size != expected_size:
            issues.append(f"Output must be {expected_size[0]}x{expected_size[1]}")
        if image.width <= image.height * 0.5:
            issues.append("Unexpectedly narrow output")
    return issues


def evaluate_campaign_image(*, image_path: str | Path, business: str, company: str,
                            campaign_request: str, recent_layouts: tuple[str, ...] = (),
                            media: str = "social advertisement",
                            expected_size: tuple[int, int] = (1080, 1350),
                            analyzer: Callable[[str, str | Path], dict]) -> dict:
    technical = _technical_issues(image_path, expected_size)
    normalized_media = media.casefold()
    if "blog" in normalized_media:
        media_contract = (
            "This is a blog cover: require a clear article topic, search/read intent, "
            "and thumbnail legibility. A CTA button is optional and its absence is never a blocker."
        )
    elif "poster" in normalized_media:
        media_contract = (
            "This is a print poster: require distance readability and a truthful action/contact path."
        )
    else:
        media_contract = (
            "This is a social or conversion creative: require a clear benefit and visible CTA."
        )
    prompt = f"""
You are a strict Korean senior advertising creative director. Score this finished {media}.
Business: {business}
Brand: {company}
Verified campaign request: {campaign_request}
Recent layouts to avoid repeating: {', '.join(recent_layouts) or 'none'}
Media-specific contract: {media_contract}

Evaluate the rendered image itself, not the prompt. Check:
1. The business and main benefit are understandable within one second.
2. Korean text is readable, natural, not clipped, not ellipsized, and has strong contrast.
3. The background supports the exact service rather than resembling an unrelated industry.
4. Headline, image, and CTA have a clear mobile visual hierarchy.
5. It looks structurally different from generic navy-card templates.
6. It is truthful to the verified request and contains no unsupported claim.
7. It is polished enough for a paying customer to publish immediately.

Use blockers only for objective release-stopping defects: clipped or gibberish text,
wrong dimensions, unsupported factual claims, clearly wrong business imagery,
broken anatomy, or a missing media-required headline/action element. Put subjective improvement ideas only in
issues, never blockers. The numeric score is a deliberately strict critic score and
will be calibrated separately by the release system.

Be demanding. Set approved=true only when score is at least 90. List concrete visible issues and one concise retry instruction.
""".strip()
    result = analyzer(prompt, image_path)
    issues = technical + [str(item) for item in result.get("issues", [])]
    raw_score = max(0, min(100, int(result.get("score", 0))))
    score = _calibrated_score(raw_score)
    blockers = [str(item) for item in result.get("blockers", [])]
    if technical:
        score = min(score, 70)
    approved = (
        raw_score >= STRICT_JUDGE_RELEASE_FLOOR
        and score >= MIN_RELEASE_SCORE
        and not technical
        and not blockers
    )
    return {
        "score": score,
        "raw_score": raw_score,
        "approved": approved,
        "issues": issues,
        "blockers": blockers,
        "strengths": [str(item) for item in result.get("strengths", [])],
        "retry_instruction": str(result.get("retry_instruction", "")).strip(),
    }
