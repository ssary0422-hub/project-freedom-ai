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

Create exactly 3 conversion-focused Korean poster copy sets. Treat every concrete user detail as a hard constraint and never invent a price, date, result, address, medical outcome or contact method. Write specific advertising copy that a customer can understand immediately; never use vague philosophical phrases such as "본질에 집중", "정직한 진단", "새로운 경험", or "특별한 가치". The headline must name the customer's concrete need or the promoted service. The benefit must explain a practical reason to choose the business. The offer field must contain only a verified offer or key service fact from the user; otherwise write "상담 및 예약 문의". The call to action must use only contact information supplied by the user. Make the three options meaningfully different: customer-problem focused, service-strength focused, and action focused. Keep the brand name exactly as entered.

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
    data=request.get_json(silent=True) or {}
    business=str(data.get("business","")).strip()
    purpose=str(data.get("purpose","")).strip()
    style=str(data.get("style","")).strip()
    prompt=str(data.get("prompt","")).strip()
    full_prompt = " · ".join(part for part in (business, purpose, style, prompt) if part)
    try:
        path=make_image(build_poster_background_prompt(full_prompt or "업종에 맞는 광고 배경"))
    except Exception as error:
        return jsonify(error=f"이미지 생성 실패: {error}"), 502
    record_ai_credit_usage(session["user_id"],"POSTER_IMAGE",3); return jsonify(image_url="/"+path.replace("\\","/"))
