from pathlib import Path

from flask import Blueprint, jsonify, render_template, request

from routes.auth import login_required


running_form_bp = Blueprint("running_form", __name__)
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
MAX_VIDEO_BYTES = 120 * 1024 * 1024


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

    return jsonify(
        ok=True,
        stage="ready",
        pace=str(request.form.get("pace", "easy")).strip(),
        checks=[
            {"key": "file", "label": "영상 파일", "status": "pass"},
            {"key": "view", "label": "측면 촬영", "status": "pass"},
            {"key": "visual_quality", "label": "전신·발·조명 자동 검사", "status": "pending"},
        ],
        message="기본 검사를 통과했어요. 다음 단계에서 AI가 촬영 품질을 확인합니다.",
    )

