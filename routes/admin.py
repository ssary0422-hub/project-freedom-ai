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


def _get_admin_feedback_data(limit=200):
    """Return product, speaking-coach, and running-coach feedback for admins."""
    init_db()
    conn = _connect()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pf.id, pf.rating, pf.liked, pf.disliked, pf.would_use, pf.created_at,
               pf.history_id, u.username, u.email, h.business, h.company
        FROM product_feedback pf
        LEFT JOIN users u ON u.id = pf.user_id
        LEFT JOIN history h ON h.id = pf.history_id
        ORDER BY pf.id DESC LIMIT ?
    """, (int(limit),))
    reviews = cursor.fetchall()

    cursor.execute("""
        SELECT pc.id, pc.body, pc.created_at, pc.history_id, u.username, u.email,
               h.business, h.company
        FROM product_comments pc
        LEFT JOIN users u ON u.id = pc.user_id
        LEFT JOIN history h ON h.id = pc.history_id
        ORDER BY pc.id DESC LIMIT ?
    """, (int(limit),))
    comments = cursor.fetchall()

    cursor.execute("SELECT id, rating, comment, created_at FROM speaking_coach_feedback ORDER BY id DESC LIMIT ?", (int(limit),))
    speaking = cursor.fetchall()
    cursor.execute("SELECT id, rating, comment, created_at FROM running_coach_feedback ORDER BY id DESC LIMIT ?", (int(limit),))
    running = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*) AS count, COALESCE(AVG(rating), 0) AS average,
               COALESCE(SUM(CASE WHEN would_use = 1 THEN 1 ELSE 0 END), 0) AS would_use
        FROM product_feedback
    """)
    product_summary = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) AS count, COALESCE(AVG(rating), 0) AS average FROM speaking_coach_feedback")
    speaking_summary = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) AS count, COALESCE(AVG(rating), 0) AS average FROM running_coach_feedback")
    running_summary = cursor.fetchone()
    conn.close()

    return {
        "reviews": reviews,
        "comments": comments,
        "speaking": speaking,
        "running": running,
        "summary": {
            "product_count": int(product_summary["count"] or 0),
            "product_average": round(float(product_summary["average"] or 0), 1),
            "would_use": int(product_summary["would_use"] or 0),
            "speaking_count": int(speaking_summary["count"] or 0),
            "speaking_average": round(float(speaking_summary["average"] or 0), 1),
            "running_count": int(running_summary["count"] or 0),
            "running_average": round(float(running_summary["average"] or 0), 1),
        },
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


@admin_bp.route("/admin/feedback")
@admin_required
def admin_feedback():
    return render_template("admin_feedback.html", feedback=_get_admin_feedback_data())


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
