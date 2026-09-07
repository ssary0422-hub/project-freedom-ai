import os
from unittest.mock import Mock, patch

from app import app


def test_speaking_coach_api_validates_required_fields():
    client = app.test_client()
    response = client.post("/api/speaking-coach", json={})
    assert response.status_code == 400


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
@patch("routes.speaking_coach.generate_speaking_coach_json")
def test_speaking_coach_api_returns_structured_result(generate):
    generate.return_value = {
        "sentence": "대기시간이 길어지고 있어요.",
        "soft": "조금만 기다려 주세요.",
        "firm": "순서대로 최대한 빨리 안내하겠습니다.",
        "coach_note": "짧게 안내해 보세요.",
    }
    client = app.test_client()
    response = client.post("/api/speaking-coach", json={
        "person": "환자·고객",
        "situation": "진료가 밀림",
        "message": "대기시간을 안내해야 함",
        "goal": "불편하지 않게 설명하고 싶음",
        "tone": "짧고 자연스럽게",
        "quick": True,
    })
    assert response.status_code == 200
    assert response.get_json()["result"]["sentence"].startswith("대기시간")
    generate.assert_called_once()
