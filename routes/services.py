from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from database.db import _connect, init_db, save_service_lead
from database.users import is_user_admin
from routes.auth import login_required


services_bp = Blueprint("services", __name__)


@services_bp.get("/services")
def services():
    """Public, payment-free sales page used to validate service demand."""
    return render_template("services.html")


@services_bp.get("/services/sample")
def service_sample():
    return render_template("service_sample.html")


@services_bp.get("/services/sample/nail-campaign")
def nail_campaign_sample():
    return render_template("nail_campaign_sample.html")


@services_bp.post("/services/lead")
def service_lead():
    fields = {
        "name": request.form.get("name", "").strip(),
        "business_name": request.form.get("business_name", "").strip(),
        "contact": request.form.get("contact", "").strip(),
        "interest": request.form.get("interest", "").strip(),
        "message": request.form.get("message", "").strip(),
    }
    if any(not fields[key] for key in ("name", "business_name", "contact", "interest")):
        flash("이름, 사업장명, 연락처, 관심 상품을 입력해주세요.", "warning")
        return redirect(url_for("services.services") + "#pilot-form")
    if any(len(value) > 500 for value in fields.values()):
        flash("입력 내용이 너무 깁니다. 500자 이내로 작성해주세요.", "warning")
        return redirect(url_for("services.services") + "#pilot-form")
    result = save_service_lead(**fields)
    if result["ok"]:
        flash("파일럿 신청이 접수됐어요. 확인 후 연락드릴게요.", "success")
    else:
        flash("신청을 저장하지 못했어요. 잠시 후 다시 시도해주세요.", "danger")
    return redirect(url_for("services.services") + "#pilot-form")


@services_bp.get("/admin/service-leads")
@login_required
def service_leads_admin():
    if not is_user_admin(session.get("user_id")):
        abort(403)
    init_db()
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, business_name, contact, interest, message, status, created_at
        FROM service_leads
        ORDER BY id DESC
        LIMIT 200
        """
    )
    leads = cursor.fetchall()
    conn.close()
    return render_template("service_leads_admin.html", leads=leads)
