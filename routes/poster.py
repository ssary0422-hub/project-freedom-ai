from flask import Blueprint, jsonify, render_template, request, session
from ai.image import make_image
from ai.providers import generate_text
from database.users import get_plan_status, record_ai_credit_usage
from routes.auth import login_required

poster_bp = Blueprint("poster", __name__)

@poster_bp.route("/poster")
@login_required
def poster():
    return render_template("poster.html")

@poster_bp.post("/poster/suggest")
@login_required
def suggest():
    status=get_plan_status(session["user_id"],required_credits=1)
    if not status["can_generate"]: return jsonify(error="AI 크레딧이 부족합니다."),402
    data=request.get_json(silent=True) or {}; business=str(data.get("business","")).strip(); purpose=str(data.get("purpose","")).strip()
    raw=generate_text(f"Create exactly 3 concise Korean advertising poster copy sets. Business: {business}. Purpose: {purpose}. Each set is one line with headline | benefit | offer | call to action. No numbering or explanation.")
    sets=[]
    for line in raw.splitlines():
        parts=[p.strip() for p in line.strip().lstrip("-•0123456789. ").split("|")]
        if len(parts)>=4: sets.append(parts[:4])
    if not sets: return jsonify(error="문구 형식을 만들지 못했습니다."),502
    record_ai_credit_usage(session["user_id"],"POSTER_TEXT",1); return jsonify(sets=sets[:3])

@poster_bp.post("/poster/background")
@login_required
def background():
    status=get_plan_status(session["user_id"],required_credits=3)
    if not status["can_generate"]: return jsonify(error="AI 이미지용 크레딧이 부족합니다."),402
    data=request.get_json(silent=True) or {}; prompt=str(data.get("prompt","")).strip()
    try:
        path=make_image((prompt or "premium commercial advertising background")+", vertical poster, clean negative space, no text, no letters, no watermark")
    except Exception as error:
        return jsonify(error=f"이미지 생성 실패: {error}"), 502
    record_ai_credit_usage(session["user_id"],"POSTER_IMAGE",3); return jsonify(image_url="/"+path.replace("\\","/"))
