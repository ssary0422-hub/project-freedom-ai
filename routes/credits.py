import os
import uuid

from flask import (
    Blueprint,
    render_template,
    session,
    redirect,
    request,
    abort,
)

from routes.auth import login_required
from database.users import (
    add_bonus_credits,
    get_credit_transactions,
    get_plan_status,
    get_user_by_email,
    is_user_admin,
)


from database.db import (
    create_test_payment,
    get_user_payments,
)


credits_bp = Blueprint(
    "credits",
    __name__
)


CREDIT_PRODUCTS = {
    "starter": {
        "name": "Starter",
        "credits": 30,
        "amount": 4900,
    },
    "popular": {
        "name": "Popular",
        "credits": 100,
        "amount": 12900,
    },
    "business": {
        "name": "Business",
        "credits": 300,
        "amount": 29900,
    },
}


def _test_payments_enabled():
    return os.getenv(
        "ENABLE_TEST_PAYMENTS",
        "0"
    ).strip() == "1"


def _sync_credit_session(user_id):
    status = get_plan_status(user_id)

    session["plan"] = status["plan"]
    session["plan_used"] = status["used"]
    session["plan_limit"] = status["limit"]
    session["plan_remaining"] = status["remaining"]
    session["plan_percent"] = status["percent"]
    session["base_remaining"] = status["base_remaining"]
    session["bonus_balance"] = status["bonus_balance"]

    return status


@credits_bp.route("/credits")
@login_required
def credits():
    user_id = session["user_id"]
    status = _sync_credit_session(user_id)

    return render_template(
        "credits.html",
        status=status,
        transactions=get_credit_transactions(
            user_id,
            30
        ),
        is_admin=is_user_admin(user_id),
        granted=request.args.get(
            "granted",
            ""
        ),
        payment=request.args.get(
            "payment",
            ""
        ),
        payment_credits=request.args.get(
            "payment_credits",
            ""
        ),
        products=CREDIT_PRODUCTS,
        test_payments_enabled=_test_payments_enabled(),
        payments=get_user_payments(
            user_id,
            30
        ),
    )



@credits_bp.route(
    "/credits/test-purchase",
    methods=["POST"]
)
@login_required
def test_purchase():
    """
    실제 결제가 아닙니다.
    ENABLE_TEST_PAYMENTS=1 일 때만 동작하는 개발/검증용 결제 흐름입니다.
    """
    if not _test_payments_enabled():
        abort(404)

    product_code = request.form.get(
        "product_code",
        ""
    ).strip().lower()

    product = CREDIT_PRODUCTS.get(
        product_code
    )

    if not product:
        return redirect(
            "/credits?payment=invalid_product"
        )

    user_id = session["user_id"]

    # 서버에서 상품 가격/크레딧을 결정합니다.
    # 브라우저가 amount/credits 값을 보내더라도 절대 신뢰하지 않습니다.
    order_id = (
        "TEST-"
        + uuid.uuid4().hex.upper()
    )

    payment_result = create_test_payment(
        user_id=user_id,
        order_id=order_id,
        product_code=product_code,
        amount=product["amount"],
        credits=product["credits"],
    )

    if not payment_result["ok"]:
        return redirect(
            "/credits?payment=duplicate"
        )

    try:
        add_bonus_credits(
            user_id,
            product["credits"],
            kind="TEST_PAYMENT",
            note=(
                f"TEST 결제 {product['name']} "
                f"{product['amount']:,}원 / "
                f"{order_id}"
            )
        )
    except Exception:
        # 테스트 결제 기록은 남지만 충전에 실패했음을 명확히 표시합니다.
        # V2 실제 PG에서는 DB 트랜잭션/상태 전이를 더 엄격히 묶습니다.
        return redirect(
            "/credits?payment=credit_error"
        )

    _sync_credit_session(
        user_id
    )

    return redirect(
        "/credits"
        f"?payment=success"
        f"&payment_credits={product['credits']}"
    )


@credits_bp.route(
    "/credits/admin/grant",
    methods=["POST"]
)
@login_required
def admin_grant():
    admin_user_id = session["user_id"]

    if not is_user_admin(admin_user_id):
        abort(403)

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    amount = request.form.get(
        "amount",
        type=int
    )

    if (
        not email
        or not amount
        or amount <= 0
        or amount > 10000
    ):
        return redirect(
            "/credits?granted=invalid"
        )

    target = get_user_by_email(email)

    if not target:
        return redirect(
            "/credits?granted=notfound"
        )

    add_bonus_credits(
        target["id"],
        amount,
        kind="ADMIN_GRANT",
        note=(
            "관리자 테스트 지급: "
            f"{session.get('user_email', '')}"
        )
    )

    if target["id"] == admin_user_id:
        _sync_credit_session(
            admin_user_id
        )

    return redirect(
        f"/credits?granted={amount}"
    )
