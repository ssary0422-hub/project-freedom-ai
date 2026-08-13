from functools import wraps

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    abort,
)

from database.users import (
    get_admin_stats,
    get_admin_users,
    get_ai_enabled,
    set_ai_enabled,
)

from routes.auth import login_required
from services.openai_costs import get_openai_cost_status


admin_bp = Blueprint(
    "admin",
    __name__
)


def admin_required(view_function):
    @wraps(view_function)
    @login_required
    def wrapped_view(*args, **kwargs):
        if not session.get("is_admin"):
            abort(403)

        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view


@admin_bp.route("/admin")
@admin_required
def admin():
    openai_cost = get_openai_cost_status()
    auto_stopped = False

    if (
        openai_cost["connected"]
        and openai_cost.get("budget_exceeded")
        and get_ai_enabled()
    ):
        set_ai_enabled(False)
        auto_stopped = True

    return render_template(
        "admin.html",
        stats=get_admin_stats(),
        users=get_admin_users(),
        openai_cost=openai_cost,
        auto_stopped=auto_stopped
    )


@admin_bp.route(
    "/admin/ai/<state>",
    methods=["POST"]
)
@admin_required
def toggle_ai(state):
    enabled = (
        str(state).lower()
        == "on"
    )

    if enabled:
        openai_cost = get_openai_cost_status()

        if (
            openai_cost["connected"]
            and openai_cost.get("budget_exceeded")
        ):
            return render_template(
                "admin.html",
                stats=get_admin_stats(),
                users=get_admin_users(),
                openai_cost=openai_cost,
                auto_stopped=False,
                ai_start_blocked=True
            ), 409

    set_ai_enabled(enabled)

    return redirect(
        url_for("admin.admin")
    )
