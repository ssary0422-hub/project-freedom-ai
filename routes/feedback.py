from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from database.db import (
    get_history,
    get_history_item,
    get_product_comments,
    get_product_feedback,
    save_product_comment,
    save_product_feedback,
)
from routes.auth import login_required

feedback_bp = Blueprint("feedback", __name__)


def _sungeum_reply(*, rating=0, liked="", disliked="", body=""):
    text = f"{liked} {disliked} {body}".lower()
    if any(word in text for word in ("불편", "작아", "잘림", "반복", "오류", "안돼", "아쉬")) or rating <= 2:
        return "알려줘서 고마워! 🐶 불편했던 부분은 그냥 넘기지 않고 순금이가 꼭 고쳐볼게. 다음 결과에서는 더 편하게 쓸 수 있게 확인하겠어 ✨"
    if rating >= 5 or any(word in text for word in ("좋아", "최고", "예뻐", "편해", "만족")):
        return "우와, 마음에 들었다니 순금이도 꼬리가 살랑살랑해! 🐶✨ 더 좋은 결과를 만들 수 있게 계속 귀 기울일게."
    return "소중한 의견 고마워! 🐶 순금이가 하나씩 반영해서 더 쓸모 있고 귀여운 작업실로 만들어갈게 💛"


@feedback_bp.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    user_id = session["user_id"]
    if request.method == "POST":
        history_id = request.form.get("history_id", type=int)
        action = request.form.get("action", "comment")
        if action == "review":
            rating = max(1, min(5, request.form.get("rating", type=int) or 1))
            liked = request.form.get("liked", "").strip()[:2000]
            disliked = request.form.get("disliked", "").strip()[:2000]
            save_product_feedback(
                user_id, history_id, rating, liked, disliked,
                request.form.get("would_use") == "on",
            )
            flash(_sungeum_reply(rating=rating, liked=liked, disliked=disliked), "sungeum")
        else:
            body = request.form.get("body", "").strip()
            if body:
                save_product_comment(user_id, history_id, body[:3000])
                flash(_sungeum_reply(body=body), "sungeum")
        return redirect(url_for("feedback.feedback", history_id=history_id) if history_id else url_for("feedback.feedback"))

    history_id = request.args.get("history_id", type=int)
    return render_template(
        "feedback.html",
        history_list=get_history(user_id),
        selected_history_id=history_id,
        feedback_list=get_product_feedback(user_id, history_id),
        comment_list=get_product_comments(user_id, history_id),
    )


@feedback_bp.route("/feedback/quick", methods=["POST"])
@login_required
def quick_feedback():
    """Save the lightweight, in-context feedback shown after a result."""
    rating = max(1, min(5, request.form.get("rating", type=int) or 3))
    history_id = request.form.get("history_id", type=int)
    if history_id and not get_history_item(history_id, session["user_id"]):
        return jsonify({"ok": False, "error": "history_not_found"}), 404
    liked = request.form.get("liked", "").strip()[:2000]
    disliked = request.form.get("disliked", "").strip()[:2000]
    comment = request.form.get("comment", "").strip()[:3000]
    save_product_feedback(
        session["user_id"], history_id, rating, liked, disliked,
        request.form.get("would_use") == "on",
    )
    if comment:
        save_product_comment(session["user_id"], history_id, comment)
    return jsonify({"ok": True, "reply": _sungeum_reply(rating=rating, liked=liked, disliked=disliked, body=comment)})
