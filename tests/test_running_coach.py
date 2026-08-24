from routes.running_coach import _fallback_plan


def test_fallback_plan_is_free_and_safe_for_tired_runner():
    result = _fallback_plan({"condition": "tired", "minutes": 30, "goal": "easy"})
    assert result["title"]
    assert "멈추세요" in result["intensity"]
    assert result["plan"]


def test_fallback_plan_supports_training_goal():
    result = _fallback_plan({"condition": "good", "minutes": 45, "goal": "fitness"})
    assert result["warmup"]
    assert "꾸준히" in result["plan"]
