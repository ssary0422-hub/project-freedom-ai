import sqlite3
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
    is_user_admin,
)

from database.db import _connect, init_db

from routes.auth import login_required
from services.openai_costs import get_openai_cost_status


admin_bp = Blueprint(
    "admin",
    __name__
)



def _get_admin_payment_data(limit=100):
    """
    ADMIN 결제 요약 + 최근 결제 목록.
    payments 테이블이 없더라도 init_db()가 먼저 생성합니다.
    """
    init_db()

    conn = _connect()
    if isinstance(conn, sqlite3.Connection):
        conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS total_count,
            COALESCE(SUM(amount), 0) AS total_amount,
            COALESCE(SUM(credits), 0) AS total_credits
        FROM payments
        WHERE status = 'PAID'
    """)
    summary = cursor.fetchone()

    cursor.execute("""
        SELECT
            COUNT(*) AS today_count,
            COALESCE(SUM(amount), 0) AS today_amount
        FROM payments
        WHERE status = 'PAID'
          AND DATE(paid_at) = CURRENT_DATE
    """)
    today = cursor.fetchone()

    cursor.execute("""
        SELECT
            p.id,
            p.order_id,
            p.product_code,
            p.amount,
            p.credits,
            p.status,
            p.provider,
            p.created_at,
            p.paid_at,
            u.id AS user_id,
            u.username,
            u.email
        FROM payments p
        LEFT JOIN users u
            ON u.id = p.user_id
        ORDER BY p.id DESC
        LIMIT ?
    """, (int(limit),))

    payments = cursor.fetchall()
    conn.close()

    return {
        "summary": {
            "total_count": int(summary["total_count"] or 0),
            "total_amount": int(summary["total_amount"] or 0),
            "total_credits": int(summary["total_credits"] or 0),
            "today_count": int(today["today_count"] or 0),
            "today_amount": int(today["today_amount"] or 0),
        },
        "payments": payments,
    }




def admin_required(view_function):
    @wraps(view_function)
    @login_required
    def wrapped_view(*args, **kwargs):
        user_id = session.get("user_id")

        if not user_id or not is_user_admin(user_id):
            session["is_admin"] = False
            abort(403)

        session["is_admin"] = True

        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view


@admin_bp.route("/admin")
@admin_required
def admin():
    openai_cost = get_openai_cost_status()
    payment_data = _get_admin_payment_data()
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
        auto_stopped=auto_stopped,
        payment_summary=payment_data["summary"],
        payments=payment_data["payments"]
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
                ai_start_blocked=True,
                payment_summary=_get_admin_payment_data()["summary"],
                payments=_get_admin_payment_data()["payments"]
            ), 409

    set_ai_enabled(enabled)

    return redirect(
        url_for("admin.admin")
    )
