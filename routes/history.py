from flask import Blueprint, render_template, redirect, url_for, session

from database.db import (
    get_history,
    delete_history_by_id
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