from pathlib import Path

import pytest

from services.campaign_art_direction import ArtDirection
from services.campaign_budget import generate_with_bounded_backgrounds


def _direction(name):
    return ArtDirection(
        concept_name=name, campaign_angle=f"angle {name}", layout_family="full_bleed_photo",
        message_angle="customer_outcome", photo_strategy=f"photo {name}", subject_position="right",
        headline_position="left", mood="clear", headline="Headline", supporting_copy="Proof",
        cta="Start", palette=("#071827", "#59e1cb", "#ffffff"), avoid=(),
    )


def test_one_background_is_reused_across_three_layouts(tmp_path):
    backgrounds = []
    rendered_backgrounds = []

    def generate(prompt):
        backgrounds.append(prompt)
        return tmp_path / "background.png"

    def render(background, direction, round_index, direction_index):
        rendered_backgrounds.append(background)
        return tmp_path / f"candidate-{direction_index}.png"

    scores = iter((70, 75, 91))
    result = generate_with_bounded_backgrounds(
        directions=[_direction("a"), _direction("b"), _direction("c")],
        generate_background=generate,
        render_candidate=render,
        evaluate_candidate=lambda _: {"score": next(scores), "approved": len(rendered_backgrounds) == 3, "retry_instruction": ""},
    )
    assert result.background_generations == 1
    assert result.rendered_candidates == 3
    assert len(backgrounds) == 1
    assert len(set(rendered_backgrounds)) == 1


def test_generation_stops_after_two_backgrounds(tmp_path):
    calls = []
    with pytest.raises(ValueError, match="안전 한도 2회"):
        generate_with_bounded_backgrounds(
            directions=[_direction("a"), _direction("b"), _direction("c")],
            generate_background=lambda prompt: calls.append(prompt) or tmp_path / f"bg-{len(calls)}.png",
            render_candidate=lambda background, direction, round_index, direction_index: tmp_path / f"{round_index}-{direction_index}.png",
            evaluate_candidate=lambda _: {"score": 80, "approved": False, "retry_instruction": "use cleaner space"},
        )
    assert len(calls) == 2
    assert "use cleaner space" in calls[1]


def test_uploaded_photo_never_calls_image_generator(tmp_path):
    calls = []
    result = generate_with_bounded_backgrounds(
        directions=[_direction("a")],
        uploaded_background=tmp_path / "real.png",
        generate_background=lambda prompt: calls.append(prompt),
        render_candidate=lambda background, direction, round_index, direction_index: tmp_path / "out.png",
        evaluate_candidate=lambda _: {"score": 92, "approved": True, "retry_instruction": ""},
    )
    assert calls == []
    assert result.background_generations == 0


def test_safe_background_can_ship_without_third_paid_generation(tmp_path):
    generated = []
    reviews = iter([
        *({"score": 80, "approved": False, "retry_instruction": "cleaner"} for _ in range(6)),
        {"score": 92, "approved": True, "retry_instruction": ""},
    ])
    result = generate_with_bounded_backgrounds(
        directions=[_direction("a"), _direction("b"), _direction("c")],
        generate_background=lambda prompt: generated.append(prompt) or tmp_path / f"paid-{len(generated)}.png",
        create_safe_background=lambda direction: tmp_path / "safe.png",
        render_candidate=lambda background, direction, round_index, direction_index: tmp_path / f"{round_index}-{direction_index}.png",
        evaluate_candidate=lambda _: next(reviews),
    )
    assert result.used_safe_fallback is True
    assert result.background_generations == 2
    assert len(generated) == 2
