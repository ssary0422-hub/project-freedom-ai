from flask import Blueprint, jsonify, render_template, request

from ai.providers import generate_speaking_coach_json
from database.db import save_speaking_coach_feedback


speaking_coach_bp = Blueprint("speaking_coach", __name__)


@speaking_coach_bp.get("/speaking-coach")
def speaking_coach():
    """Public MVP shell for Sungeum's conversational speaking coach."""
    return render_template("speaking_coach_v2.html")


@speaking_coach_bp.post("/api/speaking-coach")
def speaking_coach_api():
    """Return AI-generated lines without storing the user's private situation."""
    data = request.get_json(silent=True) or {}
    fields = {key: str(data.get(key, "")).strip() for key in ("person", "situation", "message", "goal", "tone")}
    if any(not value for value in fields.values()):
        return jsonify({"error": "person, situation, message, goal, tone are required."}), 400
    if any(len(value) > 800 for value in fields.values()):
        return jsonify({"error": "입력은 항목마다 800자 이내로 작성해 주세요."}), 400
    quick = bool(data.get("quick", False))
    try:
        result = generate_speaking_coach_json(**fields, quick=quick)
    except RuntimeError as exc:
        return jsonify({"error": str(exc), "fallback": True}), 503
    return jsonify({"result": result, "quick": quick})


@speaking_coach_bp.post("/api/speaking-coach/feedback")
def speaking_coach_feedback_api():
    """Accept one short, anonymous review after a speaking-coach result."""
    data = request.get_json(silent=True) or {}
    try:
        rating = max(1, min(5, int(data.get("rating", 0))))
    except (TypeError, ValueError):
        return jsonify({"error": "rating must be between 1 and 5."}), 400
    comment = str(data.get("comment", "")).strip()[:3000]
    if not comment and rating <= 2:
        return jsonify({"error": "짧은 개선 의견을 남겨주세요."}), 400
    save_speaking_coach_feedback(rating, comment)
    return jsonify({"ok": True, "reply": "소중한 후기 고마워! 🐶 다음 말도 더 잘 도와줄게."})
