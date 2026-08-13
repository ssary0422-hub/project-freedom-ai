from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    current_app,
    abort,
)

from database.users import (
    get_plan_status,
    set_user_plan,
)

from routes.auth import login_required


plan_bp = Blueprint(
    "plan",
    __name__
)


def _refresh_plan_session():
    status = get_plan_status(
        session["user_id"]
    )

    session["plan"] = status["plan"]
    session["plan_used"] = status["used"]
    session["plan_limit"] = status["limit"]
    session["plan_remaining"] = status["remaining"]
    session["plan_percent"] = status["percent"]

    return status


@plan_bp.route("/upgrade")
@login_required
def upgrade():
    status = _refresh_plan_session()

    return render_template(
        "upgrade.html",
        plan_status=status,
        test_mode=current_app.debug
    )


@plan_bp.route(
    "/plan/test/<plan>",
    methods=["POST"]
)
@login_required
def test_plan(plan):
    """
    로컬 개발 모드에서만 사용할 수 있는 FREE/PRO 전환 기능.
    실제 배포 환경에서는 자동으로 404 처리됩니다.
    """
    if not current_app.debug:
        abort(404)

    plan = (
        plan
        or ""
    ).upper()

    if plan not in {
        "FREE",
        "PRO",
    }:
        abort(400)

    set_user_plan(
        session["user_id"],
        plan
    )

    _refresh_plan_session()

    return redirect(
        url_for("plan.upgrade")
    )
