from io import BytesIO

from flask import Blueprint, render_template, redirect, url_for, session, send_file, request

from database.db import (
    get_history,
    delete_history_by_id,
    get_history_image,
)
from routes.auth import login_required


history_bp = Blueprint(
    "history",
    __name__
)


@history_bp.route("/history")
@login_required
def history():
    history_list = get_history(
        session["user_id"]
    )

    return render_template(
        "history.html",
        history_list=history_list
    )


@history_bp.route("/delete/<int:id>")
@login_required
def delete_history(id):
    delete_history_by_id(
        id,
        session["user_id"]
    )

    return redirect(
        url_for("history.history")
    )


@history_bp.get("/history/image/<int:history_id>")
@login_required
def history_image(history_id):
    payload = get_history_image(history_id, session["user_id"])
    if not payload:
        return "저장된 이미지가 없습니다.", 404
    data, mime = payload
    extension = ".png" if mime == "image/png" else ".jpg"
    return send_file(
        BytesIO(data),
        mimetype=mime,
        max_age=31536000,
        as_attachment=request.args.get("download") == "1",
        download_name=f"project-freedom-ai-{history_id}{extension}",
    )
