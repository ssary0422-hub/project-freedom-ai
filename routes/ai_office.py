from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ai.company import run_company_task
from database.ai_office import (
    approve_ai_office_task,
    list_ai_office_tasks,
    save_ai_office_task,
)
from routes.auth import login_required


ai_office_bp = Blueprint("ai_office", __name__, url_prefix="/ai-office")


@ai_office_bp.route("", methods=["GET", "POST"])
@login_required
def index():
    error = ""
    objective = ""
    context = ""
    if request.method == "POST":
        objective = request.form.get("objective", "").strip()
        context = request.form.get("context", "").strip()
        if len(objective) < 5:
            error = "대표 업무를 5자 이상 입력해 주세요."
        else:
            try:
                result = run_company_task(objective, context)
                save_ai_office_task(
                    session["user_id"], objective, context, result
                )
                return redirect(url_for("ai_office.index"))
            except Exception as exc:
                error = f"AI 본부가 업무를 완료하지 못했습니다: {exc}"

    return render_template(
        "ai_office.html",
        error=error,
        objective=objective,
        context=context,
        tasks=list_ai_office_tasks(session["user_id"]),
    )


@ai_office_bp.post("/<int:task_id>/approve")
@login_required
def approve(task_id):
    if approve_ai_office_task(task_id, session["user_id"]):
        flash("대표 승인이 기록되었습니다.", "success")
    else:
        flash("승인할 업무를 찾을 수 없거나 이미 승인되었습니다.", "warning")
    return redirect(url_for("ai_office.index"))
