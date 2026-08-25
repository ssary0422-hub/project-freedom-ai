"""Free, no-video conversational running coach."""

from flask import Blueprint, jsonify, render_template, request, session

from ai.providers import generate_running_coach_json
from database.db import save_running_coach_feedback
from i18n.running_coach_copy import RUNNING_COACH_COPY

FALLBACK_DETAILS = {
    "en": ("{minutes} minutes at an easy pace, with a short walk whenever needed.", "5 minutes of easy walking before you start.", "Stop if pain increases and rest if you feel unwell.", "Walk slowly for 5 minutes and stretch gently."),
    "ja": ("{minutes}分を無理のないペースで走り、必要なら短く歩きましょう。", "開始前に5分ゆっくり歩きます。", "痛みが強くなったら中止して休んでください。", "5分ゆっくり歩いて軽くストレッチします。"),
    "th": ("วิ่ง {minutes} นาทีด้วยความเร็วสบาย ๆ และเดินพักสั้น ๆ เมื่อจำเป็น", "เดินเบา ๆ 5 นาทีก่อนเริ่มวิ่ง", "หากอาการปวดเพิ่มขึ้นให้หยุดและพักทันที", "เดินช้า ๆ 5 นาทีแล้วค่อยยืดกล้ามเนื้อเบา ๆ"),
    "zh": ("以轻松速度跑{minutes}分钟，需要时短暂步行休息。", "开始前轻松步行5分钟。", "疼痛加重或不舒服时请停止并休息。", "慢走5分钟并轻柔拉伸。"),
    "es": ("Corre {minutes} minutos a un ritmo suave y camina un poco cuando lo necesites.", "Camina suavemente 5 minutos antes de empezar.", "Si aumenta el dolor, detente y descansa.", "Camina despacio 5 minutos y estira suavemente."),
}


running_coach_bp = Blueprint("running_coach", __name__)


def _fallback_plan(payload: dict) -> dict:
    condition = str(payload.get("condition", "normal")).strip().lower()
    minutes = max(10, min(120, int(payload.get("minutes", 30) or 30)))
    goal = str(payload.get("goal", "easy")).strip().lower()
    language = session.get("language", "ko")
    copy = RUNNING_COACH_COPY.get(language, RUNNING_COACH_COPY["ko"])
    if language != "ko":
        body, warmup, caution, cooldown = FALLBACK_DETAILS.get(language, FALLBACK_DETAILS["en"])
        return {
            "title": copy["plan"],
            "plan": body.format(minutes=minutes),
            "intensity": copy["easy"],
            "warmup": warmup,
            "caution": caution,
            "cooldown": cooldown,
            "cheer": copy["fallback"],
        }
    if condition in {"tired", "pain"}:
        intensity = "걷기와 아주 느린 조깅을 번갈아 하세요. 통증이 있으면 달리기를 멈추세요."
        plan = f"{min(minutes, 25)}분 가볍게 걷고, 몸이 괜찮을 때만 1~2분씩 천천히 조깅해요."
    elif goal in {"fitness", "race"}:
        intensity = "숨이 차지만 짧은 문장은 말할 수 있는 정도로 달려요."
        plan = f"10분 워밍업 후 {max(10, minutes - 20)}분 꾸준히 달리고, 10분 천천히 마무리해요."
    else:
        intensity = "대화가 가능한 편안한 강도로 달려요."
        plan = f"처음 5분은 천천히, 이후 {max(5, minutes - 10)}분 편안하게 달리고 5분 걸으며 마무리해요."
    return {
        "title": "오늘의 러닝 제안",
        "plan": plan,
        "intensity": intensity,
        "warmup": "발목 돌리기와 가벼운 걷기로 5분 몸을 깨워요.",
        "caution": "날카로운 통증, 어지러움, 호흡 곤란이 있으면 즉시 멈추고 휴식하세요.",
        "cooldown": "5분 걷기 후 종아리와 허벅지를 가볍게 풀어주세요.",
        "cheer": "오늘의 목표는 완주가 아니라 내 몸과 대화하는 거예요. 순금이가 응원할게요!",
    }


@running_coach_bp.get("/running-coach")
def running_coach():
    return render_template("running_coach.html")


@running_coach_bp.get("/running-route")
def running_route():
    """GPS-assisted route recommendation MVP (free, no credit charge)."""
    return render_template("running_route.html")


@running_coach_bp.post("/running-coach/analyze")
def analyze_running_coach():
    payload = request.get_json(silent=True) or {}
    try:
        minutes = int(payload.get("minutes", 30))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="러닝 시간을 확인해 주세요."), 400
    normalized = {
        "condition": str(payload.get("condition", "normal"))[:20],
        "minutes": max(10, min(120, minutes)),
        "goal": str(payload.get("goal", "easy"))[:20],
    }
    fallback = _fallback_plan(normalized)
    try:
        result = generate_running_coach_json(**normalized)
        if not isinstance(result, dict):
            raise RuntimeError("invalid result")
        # Never show an AI response in the wrong script.  The provider can
        # occasionally return legacy Korean/garbled text even when Thai is
        # selected, so fall back to the verified Thai plan in that case.
        if session.get("language") == "th":
            combined = " ".join(str(value) for value in result.values())
            if not any("\u0e00" <= char <= "\u0e7f" for char in combined):
                raise RuntimeError("localized result unavailable")
        result = {**fallback, **{key: str(value).strip() for key, value in result.items() if value}}
        source = "ai"
    except Exception:
        result = fallback
        source = "fallback"
    return jsonify(ok=True, result=result, source=source, credits_used=0, free_feature=True)


@running_coach_bp.post("/api/running-coach/feedback")
def running_coach_feedback():
    data = request.get_json(silent=True) or {}
    try:
        rating = max(1, min(5, int(data.get("rating", 0))))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="rating must be between 1 and 5."), 400
    comment = str(data.get("comment", "")).strip()[:3000]
    if not comment and rating <= 2:
        return jsonify(ok=False, error="짧은 개선 의견을 남겨주세요."), 400
    save_running_coach_feedback(rating, comment)
    return jsonify(ok=True)
