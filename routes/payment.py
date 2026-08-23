import base64
import os
import uuid
from datetime import datetime, timedelta

import requests
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from routes.auth import login_required
from database.db import (
    complete_payment,
    create_pending_payment,
    get_payment_by_order,
)
from database.users import set_user_plan


payment_bp = Blueprint("payment", __name__)

PRODUCTS = {
    "sungeum_pro_monthly": {
        "name": "순금이 프로 1개월",
        "amount": 9900,
        "description": "순금이 코치 고급 기능 1개월",
    },
}


def _client_key():
    return os.environ.get("TOSS_CLIENT_KEY", "").strip()


@payment_bp.route("/payment")
@login_required
def payment_page():
    return render_template(
        "payment.html",
        client_key=_client_key(),
        products=PRODUCTS,
        user_email=session.get("user_email", ""),
    )


@payment_bp.route("/api/payment/order", methods=["POST"])
@login_required
def create_order():
    payload = request.get_json(silent=True) or {}
    product_code = str(payload.get("product_code", "")).strip()
    product = PRODUCTS.get(product_code)
    if not product:
        return jsonify({"ok": False, "message": "유효하지 않은 상품입니다."}), 400

    order_id = "PFA-" + uuid.uuid4().hex[:24].upper()
    result = create_pending_payment(
        user_id=session["user_id"],
        order_id=order_id,
        product_code=product_code,
        amount=product["amount"],
    )
    if not result["ok"]:
        return jsonify({"ok": False, "message": "주문을 만들지 못했습니다."}), 409
    return jsonify({"ok": True, "order_id": order_id, **product})


@payment_bp.route("/payment/success")
@login_required
def payment_success():
    return render_template("payment_success.html", query=request.args)


@payment_bp.route("/payment/fail")
@login_required
def payment_fail():
    return render_template("payment_fail.html", query=request.args)


@payment_bp.route("/api/payment/confirm", methods=["POST"])
@login_required
def confirm_payment():
    payload = request.get_json(silent=True) or {}
    payment_key = str(payload.get("paymentKey", "")).strip()
    order_id = str(payload.get("orderId", "")).strip()
    amount = payload.get("amount")
    if not payment_key or not order_id or not isinstance(amount, int):
        return jsonify({"ok": False, "message": "결제 정보가 올바르지 않습니다."}), 400

    order = get_payment_by_order(order_id, session["user_id"])
    if not order or int(order[5]) != amount:
        return jsonify({"ok": False, "message": "주문 금액을 확인할 수 없습니다."}), 400
    if order[7] == "PAID":
        return jsonify({"ok": True, "already_paid": True})

    secret_key = os.environ.get("TOSS_SECRET_KEY", "").strip()
    if not secret_key:
        return jsonify({"ok": False, "message": "TOSS_SECRET_KEY가 설정되지 않았습니다."}), 503

    encoded = base64.b64encode(f"{secret_key}:".encode()).decode()
    try:
        response = requests.post(
            "https://api.tosspayments.com/v1/payments/confirm",
            headers={"Authorization": f"Basic {encoded}", "Content-Type": "application/json"},
            json={"paymentKey": payment_key, "orderId": order_id, "amount": amount},
            timeout=15,
        )
        response_data = response.json()
    except (requests.RequestException, ValueError):
        return jsonify({"ok": False, "message": "결제 승인 서버와 통신하지 못했습니다."}), 502

    if response.status_code >= 400:
        return jsonify({"ok": False, "message": response_data.get("message", "결제 승인이 거절되었습니다.")}), 400

    saved = complete_payment(order_id, payment_key)
    if not saved["ok"] and not saved["already_paid"]:
        return jsonify({"ok": False, "message": "결제는 승인됐지만 주문 기록 저장에 실패했습니다."}), 500
    if saved["ok"]:
        expires_at = (datetime.now() + timedelta(days=30)).isoformat(timespec="seconds")
        set_user_plan(session["user_id"], "PRO", expires_at=expires_at)
    return jsonify({"ok": True, "payment": response_data})
