import base64
import binascii
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, jsonify, render_template, request, session
from ai.image import make_image
from ai.providers import generate_text
from ai.image_prompts import build_poster_background_prompt
from database.users import get_plan_status, record_ai_credit_usage
from database.db import save_history
from routes.auth import login_required

poster_bp = Blueprint("poster", __name__)

def _save_poster_result_image(data_url, user_id):
    prefix = "data:image/png;base64,"
    if not isinstance(data_url, str) or not data_url.startswith(prefix):
        raise ValueError("PNG 포스터 결과만 저장할 수 있어요.")
    try:
        image_bytes = base64.b64decode(data_url[len(prefix):], validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("포스터 이미지 형식을 확인하지 못했어요.") from exc
    if not image_bytes or len(image_bytes) > 8 * 1024 * 1024 or not image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("포스터 이미지가 비어 있거나 저장 가능한 크기를 넘었어요.")
    relative = Path("generated") / "poster" / str(user_id) / f"{uuid4().hex}.png"
    target = Path("static") / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(image_bytes)
    return f"/static/{relative.as_posix()}"

def _compact_copy(value, limit, fallback=""):
    text = " ".join(str(value or "").split()).strip(" -•")
    if not text:
        return fallback
    if len(text) <= limit:
        return text
    shortened = text[:limit + 1].rsplit(" ", 1)[0]
    return (shortened if len(shortened) >= limit // 2 else text[:limit]).rstrip(" ,.!?")

def _format_contact(value):
    text = " ".join(str(value or "").split())
    digits = "".join(character for character in text if character.isdigit())
    if len(digits) == 11 and digits.startswith("01"):
        phone = f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        return f"예약 문의 {phone}"
    if len(digits) == 10 and digits.startswith("0"):
        phone = f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        return f"예약 문의 {phone}"
    return _compact_copy(text, 28, "상담 및 예약 문의")

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

Create exactly 3 conversion-focused Korean poster copy sets. Treat every concrete user detail as a hard constraint and never invent a price, date, result, address, medical outcome or contact method. Rewrite the request as polished advertising copy instead of copying the user's wording or writing a search query. Never use vague phrases such as "본질에 집중", "정직한 진단", "새로운 경험", "특별한 가치", "가성비 좋고", or "전문적인" unless the user supplied objective evidence. The headline must express one clear customer need or outcome in at most 18 Korean characters. The benefit must give one concrete reason to visit in at most 36 characters. The offer must be a short verified offer or service fact in at most 16 characters; if none was supplied, write "지금 예약하기". The contact field must contain only the supplied contact information, formatted for readability, in at most 28 characters. Never repeat the company name in the headline, benefit or offer. Make the three options meaningfully different: customer-problem focused, service-strength focused, and action focused. Keep the brand name exactly as entered.

Return exactly one option per line using this format only:
headline | customer benefit | offer or key fact | call to action
No numbering and no explanation.
""")
    sets=[]
    for line in raw.splitlines():
        parts=[p.strip() for p in line.strip().lstrip("-•0123456789. ").split("|")]
        if len(parts)>=4:
            sets.append([
                _compact_copy(parts[0], 22, "지금 필요한 서비스를 만나보세요"),
                _compact_copy(parts[1], 42, "편안하게 상담받아 보세요"),
                _compact_copy(parts[2], 18, "지금 예약하기"),
                _format_contact(parts[3]),
            ])
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

@poster_bp.post("/poster/history")
@login_required
def save_poster_history():
    data = request.get_json(silent=True) or {}
    company = str(data.get("company", "")).strip()[:120]
    headline = str(data.get("headline", "")).strip()[:240]
    benefit = str(data.get("benefit", "")).strip()[:500]
    if not company or not headline or not data.get("image"):
        return jsonify(ok=False, error="완성된 포스터 정보가 부족해요."), 400
    try:
        image_url = _save_poster_result_image(data["image"], session["user_id"])
    except (TypeError, ValueError) as exc:
        return jsonify(ok=False, error=str(exc)), 400
    offer = str(data.get("offer", "")).strip()[:240]
    contact = str(data.get("contact", "")).strip()[:240]
    result = f"포스터 제목: {headline}\n핵심 혜택: {benefit}\n핵심 정보: {offer or '-'}\n행동 유도: {contact or '-'}\n\n🐾 순금 검수 완료"
    history_id = save_history(
        "AI 광고 포스터", company, "순금 추천 포스터", result,
        image_url=image_url, content_type="poster", user_id=session["user_id"],
    )
    return jsonify(ok=True, history_id=history_id, image_url=image_url)
