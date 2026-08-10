from flask import Blueprint, render_template, redirect, url_for

from database.db import (
    get_history,
    delete_history_by_id
)


history_bp = Blueprint(
    "history",
    __name__
)


@history_bp.route("/history")
def history():
    history_list = get_history()

    return render_template(
        "history.html",
        history_list=history_list
    )


@history_bp.route("/delete/<int:id>")
def delete_history(id):
    delete_history_by_id(id)

    return redirect(
        url_for("history.history")
    )