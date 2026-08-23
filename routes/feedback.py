from flask import Blueprint, redirect, render_template, request, session, url_for

from database.db import (
    get_history,
    get_product_comments,
    get_product_feedback,
    save_product_comment,
    save_product_feedback,
)
from routes.auth import login_required

feedback_bp = Blueprint("feedback", __name__)


@feedback_bp.route("/feedback", methods=["GET", "POST"])
@login_required
def feedback():
    user_id = session["user_id"]
    if request.method == "POST":
        history_id = request.form.get("history_id", type=int)
        action = request.form.get("action", "comment")
        if action == "review":
            rating = max(1, min(5, request.form.get("rating", type=int) or 1))
            save_product_feedback(
                user_id, history_id, rating,
                request.form.get("liked", "").strip()[:2000],
                request.form.get("disliked", "").strip()[:2000],
                request.form.get("would_use") == "on",
            )
        else:
            body = request.form.get("body", "").strip()
            if body:
                save_product_comment(user_id, history_id, body[:3000])
        return redirect(url_for("feedback.feedback", history_id=history_id) if history_id else url_for("feedback.feedback"))

    history_id = request.args.get("history_id", type=int)
    return render_template(
        "feedback.html",
        history_list=get_history(user_id),
        selected_history_id=history_id,
        feedback_list=get_product_feedback(user_id, history_id),
        comment_list=get_product_comments(user_id, history_id),
    )
