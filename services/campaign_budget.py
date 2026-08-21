"""Bound expensive campaign image generation while preserving layout variety."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from services.campaign_art_direction import ArtDirection
from services.campaign_quality import evaluate_campaign_image


MAX_BACKGROUND_GENERATIONS = 2


@dataclass(frozen=True)
class BudgetedCampaignResult:
    output_path: Path
    review: dict
    background_generations: int
    rendered_candidates: int
    used_safe_fallback: bool = False


def generate_with_bounded_backgrounds(
    *,
    directions: Sequence[ArtDirection],
    generate_background: Callable[[str], str | Path],
    render_candidate: Callable[[str | Path, ArtDirection, int, int], str | Path],
    evaluate_candidate: Callable[[str | Path], dict],
    uploaded_background: str | Path | None = None,
    create_safe_background: Callable[[ArtDirection], str | Path] | None = None,
    max_background_generations: int = MAX_BACKGROUND_GENERATIONS,
) -> BudgetedCampaignResult:
    """Reuse each costly background across all layouts and stop after two generations.

    The inexpensive deterministic renderer may create several layouts. Only the
    background model is capped because it dominates provider cost. The best
    failed review supplies focused guidance for the one permitted retry.
    """
    if not directions:
        raise ValueError("At least one art direction is required")
    if max_background_generations < 1:
        raise ValueError("At least one background attempt is required")

    generated = 0
    rendered = 0
    failures: list[tuple[Path, dict]] = []
    retry_instruction = ""
    rounds = 1 if uploaded_background else max_background_generations

    for round_index in range(rounds):
        if uploaded_background:
            background = Path(uploaded_background)
        else:
            prompt = directions[0].campaign_angle
            if retry_instruction:
                prompt += f". Correct the previous failure: {retry_instruction}"
            background = Path(generate_background(prompt))
            generated += 1

        for direction_index, direction in enumerate(directions):
            output = Path(render_candidate(background, direction, round_index, direction_index))
            rendered += 1
            review = evaluate_candidate(output)
            if review.get("approved"):
                return BudgetedCampaignResult(output, review, generated, rendered)
            failures.append((output, review))

        best_review = max((review for _, review in failures), key=lambda item: item.get("score", 0))
        retry_instruction = str(best_review.get("retry_instruction", "")).strip()

    if create_safe_background:
        safe_background = Path(create_safe_background(directions[0]))
        for direction_index, direction in enumerate(directions):
            output = Path(render_candidate(safe_background, direction, rounds, direction_index))
            rendered += 1
            review = evaluate_candidate(output)
            if review.get("approved"):
                return BudgetedCampaignResult(output, review, generated, rendered, True)
            failures.append((output, review))

    best_path, best_review = max(failures, key=lambda item: item[1].get("score", 0))
    raise ValueError(
        f"90점 출고 기준을 통과하지 못했습니다. 최고 점수: {best_review.get('score', 0)}점; "
        f"배경 생성은 안전 한도 {generated}회에서 중단했습니다."
    )
