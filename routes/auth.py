import os
from functools import wraps

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
)

from database.users import (
    create_user,
    verify_user,
    get_user_by_email,
    get_plan_status,
    is_user_admin,
    set_user_admin_by_email,
)


auth_bp = Blueprint(
    "auth",
    __name__
)


def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(
                url_for("auth.login")
            )

        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view



@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():
    if session.get("user_id"):
        return redirect(
            url_for("home")
        )

    error = ""
    email = ""
    username = ""

    if request.method == "POST":
        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        password_confirm = request.form.get(
            "password_confirm",
            ""
        )

        if not all([
            email,
            username,
            password,
            password_confirm,
        ]):
            error = "모든 항목을 입력해 주세요."

        elif "@" not in email:
            error = "올바른 이메일 주소를 입력해 주세요."

        elif len(username) < 2:
            error = "이름은 2글자 이상 입력해 주세요."

        elif len(password) < 8:
            error = "비밀번호는 8자 이상으로 설정해 주세요."

        elif password != password_confirm:
            error = "비밀번호 확인이 일치하지 않습니다."

        elif get_user_by_email(email):
            error = "이미 가입된 이메일입니다."

        else:
            user_id = create_user(
                email,
                username,
                password
            )

            if user_id is None:
                error = "회원가입 처리 중 오류가 발생했습니다."
            else:
                return redirect(
                    url_for(
                        "auth.login",
                        registered=1
                    )
                )

    return render_template(
        "register.html",
        error=error,
        email=email,
        username=username
    )


@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():
    if session.get("user_id"):
        return redirect(
            url_for("home")
        )

    error = ""
    email = ""
    registered = (
        request.args.get("registered")
        == "1"
    )

    if request.method == "POST":
        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = verify_user(
            email,
            password
        )

        if not user:
            error = "이메일 또는 비밀번호가 올바르지 않습니다."
        else:
            session.clear()

            session["user_id"] = user["id"]
            session["user_name"] = user["username"]
            session["user_email"] = user["email"]

            admin_email = os.environ.get(
                "ADMIN_EMAIL",
                ""
            ).strip().lower()

            if (
                admin_email
                and user["email"].strip().lower() == admin_email
            ):
                set_user_admin_by_email(
                    user["email"],
                    True
                )

            session["is_admin"] = is_user_admin(
                user["id"]
            )

            plan_status = get_plan_status(user["id"])
            session["plan"] = plan_status["plan"]
            session["plan_used"] = plan_status["used"]
            session["plan_limit"] = plan_status["limit"]
            session["plan_remaining"] = plan_status["remaining"]
            session["plan_percent"] = plan_status["percent"]

            return redirect(
                url_for("home")
            )

    return render_template(
        "login.html",
        error=error,
        email=email,
        registered=registered
    )


@auth_bp.route("/logout")
def logout():
    session.clear()

    return redirect(
        url_for("auth.login")
    )
