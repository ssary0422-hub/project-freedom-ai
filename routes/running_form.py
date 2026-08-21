import base64
import binascii
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request, session

from database.db import save_history
from database.users import get_plan_status, record_ai_credit_usage
from routes.auth import login_required


running_form_bp = Blueprint("running_form", __name__)
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
MAX_VIDEO_BYTES = 120 * 1024 * 1024
MAX_RESULT_IMAGE_BYTES = 5 * 1024 * 1024
RUNNING_FORM_CREDITS = 3


def _save_result_image(data_url, user_id):
    prefix = "data:image/png;base64,"
    if not isinstance(data_url, str) or not data_url.startswith(prefix):
        raise ValueError("PNG 결과 이미지만 저장할 수 있어요.")
    try:
        image_bytes = base64.b64decode(data_url[len(prefix):], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("결과 이미지 형식을 확인하지 못했어요.") from exc
    if not image_bytes or len(image_bytes) > MAX_RESULT_IMAGE_BYTES or not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("결과 이미지가 비어 있거나 저장 가능한 크기를 넘었어요.")
    relative = Path("generated") / "running" / str(user_id) / f"{uuid.uuid4().hex}.png"
    target = Path("static") / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(image_bytes)
    return f"/static/{relative.as_posix()}"


@running_form_bp.get("/running-form")
@login_required
def running_form():
    return render_template("running_form.html")


@running_form_bp.post("/running-form/preflight")
@login_required
def preflight():
    video = request.files.get("video")
    if not video or not video.filename:
        return jsonify(ok=False, error="러닝 영상을 선택해 주세요."), 400

    extension = Path(video.filename).suffix.lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        return jsonify(ok=False, error="MP4, MOV, M4V, WEBM 영상만 분석할 수 있어요."), 400

    video.stream.seek(0, 2)
    size = video.stream.tell()
    video.stream.seek(0)
    if size <= 0:
        return jsonify(ok=False, error="비어 있는 영상이에요."), 400
    if size > MAX_VIDEO_BYTES:
        return jsonify(ok=False, error="영상은 120MB 이하로 올려 주세요."), 413
    if str(request.form.get("view", "side")).strip() != "side":
        return jsonify(ok=False, error="첫 버전은 정확한 측면 영상만 지원해요."), 400

    credit_status = get_plan_status(session["user_id"], required_credits=RUNNING_FORM_CREDITS)
    if not credit_status["can_generate"]:
        return jsonify(
            ok=False,
            error=f"러닝폼 분석에는 {RUNNING_FORM_CREDITS}크레딧이 필요해요. 현재 {credit_status['remaining']}크레딧이 남아 있어요.",
            required_credits=RUNNING_FORM_CREDITS,
            remaining_credits=credit_status["remaining"],
        ), 402

    return jsonify(
        ok=True,
        stage="ready",
        pace=str(request.form.get("pace", "easy")).strip(),
        checks=[
            {"key": "file", "label": "영상 파일", "status": "pass"},
            {"key": "view", "label": "측면 촬영", "status": "pass"},
            {"key": "visual_quality", "label": "전신·발·조명 자동 검사", "status": "pending"},
        ],
        message="기본 검사를 통과했어요. 다음 단계에서 AI가 촬영 품질과 자세를 확인합니다.",
    )


@running_form_bp.post("/running-form/history")
@login_required
def save_running_history():
    payload = request.get_json(silent=True) or {}
    required = ("score", "runnerType", "strikeType", "averageKneeAngle", "averageTrunkLean", "strikeConfidence", "side", "image")
    if any(key not in payload for key in required):
        return jsonify(ok=False, error="러닝 분석 결과가 완성되지 않았어요."), 400
    credit_status = get_plan_status(session["user_id"], required_credits=RUNNING_FORM_CREDITS)
    if not credit_status["can_generate"]:
        return jsonify(ok=False, error=f"결과 저장에는 {RUNNING_FORM_CREDITS}크레딧이 필요해요.", required_credits=RUNNING_FORM_CREDITS), 402
    try:
        score = max(0, min(100, int(payload["score"])))
        knee = round(float(payload["averageKneeAngle"]), 1)
        trunk = round(float(payload["averageTrunkLean"]), 1)
        confidence = max(0, min(100, int(payload["strikeConfidence"])))
        image_url = _save_result_image(payload["image"], session["user_id"])
    except (TypeError, ValueError) as exc:
        return jsonify(ok=False, error=str(exc)), 400

    runner_type = str(payload["runnerType"])[:80]
    strike_type = str(payload["strikeType"])[:40]
    side = str(payload["side"])[:40]
    result = (
        f"러닝폼 종합 점수: {score}/100\n"
        f"러너 유형: {runner_type}\n착지 유형: {strike_type} · 신뢰도 {confidence}%\n"
        f"분석 방향: {side}\n무릎 각도: {knee}° · AI 참고 범위 105~125°\n"
        f"상체 기울기: {trunk}° · AI 참고 범위 6~14°\n\n"
        f"순금이의 한마디\n{str(payload.get('coachMessage', ''))[:600]}"
    )
    history_id = save_history(
        "순금이 코치의 러닝폼 리포트", "순금이 AI 러닝코치", runner_type, result,
        image_url=image_url, content_type="running_form", user_id=session["user_id"],
    )
    record_ai_credit_usage(session["user_id"], "RUNNING_FORM", RUNNING_FORM_CREDITS)
    updated_status = get_plan_status(session["user_id"])
    session["plan_used"] = updated_status["used"]
    session["plan_remaining"] = updated_status["remaining"]
    session["plan_percent"] = updated_status["percent"]
    return jsonify(ok=True, history_id=history_id, image_url=image_url, credits_used=RUNNING_FORM_CREDITS, remaining_credits=updated_status["remaining"])
