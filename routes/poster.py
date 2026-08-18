from flask import Blueprint, jsonify, render_template, request, session
from ai.image import make_image
from ai.providers import generate_text
from ai.image_prompts import build_poster_background_prompt
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
    raw=generate_text(f"""
You are a senior Korean advertising copywriter.
Company / brand: {business}
User's campaign request and mandatory details: {purpose}

Create exactly 3 premium poster copy sets. Treat every concrete user detail as a hard constraint and never invent a price, date, result, address or contact method. Make the three options meaningfully different: premium editorial, event-focused, and trust-focused. Keep the brand name exactly as entered. Use [직접 입력 필요] if a required business fact is missing.

Return exactly one option per line using this format only:
headline | customer benefit | offer or key fact | call to action
No numbering and no explanation.
""")
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
        path=make_image(build_poster_background_prompt(prompt or "premium commercial advertising background"))
    except Exception as error:
        return jsonify(error=f"이미지 생성 실패: {error}"), 502
    record_ai_credit_usage(session["user_id"],"POSTER_IMAGE",3); return jsonify(image_url="/"+path.replace("\\","/"))
