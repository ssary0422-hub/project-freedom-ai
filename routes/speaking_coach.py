from flask import Blueprint, jsonify, render_template, request

from ai.providers import generate_speaking_coach_json


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
