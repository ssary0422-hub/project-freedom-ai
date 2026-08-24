import os

from routes.ads import ads_bp
from routes.blog import blog_bp
from routes.sns import sns_bp
from routes.history import history_bp
from routes.feedback import feedback_bp
from database.db import init_db, get_dashboard_data
from routes.package import package_bp
from routes.profiles import profiles_bp
from routes.auth import auth_bp, login_required
from routes.plan import plan_bp
from routes.poster import poster_bp
from routes.brand_library import brand_library_bp
from routes.ai_office import ai_office_bp
from routes.running_form import running_form_bp
from routes.speaking_coach import speaking_coach_bp
from routes.social_publish import social_publish_bp
from routes.payment import payment_bp
from routes.services import services_bp

from i18n.translations import SUPPORTED_LANGUAGES, running_i18n, translate
from routes.admin import admin_bp
from routes.credits import credits_bp
from database.users import (
    init_users_table,
    set_user_admin_by_email,
)

from flask import (
    Flask,
    abort,
    render_template,
    request,
    send_file,
    redirect,
    session
)
from werkzeug.middleware.proxy_fix import ProxyFix
from docx import Document
from docx.shared import Inches
from documents.pdf import (
    create_pdf,
    create_blog_pdf,
    create_sns_pdf,
    PDF_PATH
)

from ai.blog import make_blog
from ai.sns import make_sns

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "project-freedom-ai-dev-secret-change-me"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production" or bool(os.environ.get("RENDER"))
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 14


@app.before_request
def protect_same_origin_writes():
    """Reject browser write requests sent from a different site.

    This protects every existing POST endpoint without requiring each form and
    fetch call to maintain a separate token. Non-browser clients without an
    Origin header remain compatible; browser-provided cross-site origins do not.
    """
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None
    origin = request.headers.get("Origin", "").rstrip("/")
    trusted_origins = {
        request.host_url.rstrip("/"),
        "https://projectfreedom-ai.com",
        "https://www.projectfreedom-ai.com",
        "https://project-freedom-ai.onrender.com",
    }
    configured_origins = os.environ.get("TRUSTED_ORIGINS", "")
    trusted_origins.update(
        item.strip().rstrip("/")
        for item in configured_origins.split(",")
        if item.strip()
    )
    if origin and origin not in trusted_origins:
        abort(403)
    return None


@app.after_request
def add_security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.is_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response

init_db()
init_users_table()

# Render/production 환경변수에 등록된 이메일을 관리자 계정으로 자동 지정
admin_email = os.environ.get("ADMIN_EMAIL", "").strip()
if admin_email:
    set_user_admin_by_email(admin_email, True)


app.register_blueprint(ads_bp)
app.register_blueprint(blog_bp)
app.register_blueprint(sns_bp)
app.register_blueprint(history_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(package_bp)
app.register_blueprint(profiles_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(plan_bp)
app.register_blueprint(poster_bp)
app.register_blueprint(brand_library_bp)
app.register_blueprint(ai_office_bp)
app.register_blueprint(running_form_bp)
app.register_blueprint(speaking_coach_bp)
app.register_blueprint(social_publish_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(services_bp)


# -------------------------
# 다국어 UI V1
# -------------------------

@app.context_processor
def inject_i18n():
    language = session.get("language", "ko")

    if language not in SUPPORTED_LANGUAGES:
        language = "ko"

    return {
        "current_language": language,
        "supported_languages": SUPPORTED_LANGUAGES,
        "t": lambda key: translate(key, language),
        "running_i18n": running_i18n(language),
    }


@app.route("/language/<language_code>")
def set_language(language_code):
    if language_code in SUPPORTED_LANGUAGES:
        session["language"] = language_code

    next_url = request.args.get("next", "").strip()

    # 외부 URL 오픈 리다이렉트 방지: 내부 경로만 허용
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = request.referrer or "/"

        # referrer가 외부 주소일 수 있으므로 최종적으로 안전하게 홈 사용
        if next_url.startswith("http://") or next_url.startswith("https://"):
            from urllib.parse import urlparse
            parsed = urlparse(next_url)
            next_url = parsed.path or "/"
            if parsed.query:
                next_url += "?" + parsed.query

    return redirect(next_url)



app.register_blueprint(admin_bp)
app.register_blueprint(credits_bp)

WORD_PATH = "downloads/advertisement.docx"
BLOG_WORD_PATH = "downloads/blog.docx"
SNS_WORD_PATH = "downloads/sns.docx"

# -------------------------
# 데이터베이스
# -------------------------

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/terms")
def terms():
    return render_template("policy.html", policy="terms")


@app.route("/privacy")
def privacy():
    return render_template("policy.html", policy="privacy")


@app.route("/refund-policy")
def refund_policy():
    return render_template("policy.html", policy="refund")


@app.route("/dashboard")
@login_required
def dashboard():
    dashboard_data = get_dashboard_data(session["user_id"])
    return render_template("dashboard.html", dashboard=dashboard_data)

# -------------------------
# Word 문서
# -------------------------

def create_word(result, image_path=""):
    os.makedirs("downloads", exist_ok=True)

    document = Document()

    # 제목
    document.add_heading(
        "Project Freedom AI",
        level=1
    )

    # AI 이미지
    if image_path and os.path.exists(image_path):
        document.add_picture(
            image_path,
            width=Inches(5.5)
        )

    # 광고 문구
    document.add_paragraph(result)

    # 저장
    document.save(WORD_PATH)

    return WORD_PATH


def create_blog_word(result, image_path=""):
    os.makedirs("downloads", exist_ok=True)

    document = Document()

    document.add_heading(
        "Project Freedom AI - Blog",
        level=1
    )

    if image_path and os.path.exists(image_path):
        document.add_picture(
            image_path,
            width=Inches(5.5)
        )

    document.add_paragraph(result)

    document.save(BLOG_WORD_PATH)

    return BLOG_WORD_PATH


def create_sns_word(result, image_path=""):
    os.makedirs("downloads", exist_ok=True)

    document = Document()

    document.add_heading(
        "Project Freedom AI - SNS",
        level=1
    )

    if image_path and os.path.exists(image_path):
        document.add_picture(
            image_path,
            width=Inches(5.5)
        )

    document.add_paragraph(result)

    document.save(SNS_WORD_PATH)

    return SNS_WORD_PATH


# -------------------------
# 광고 생성 페이지
# -------------------------

def _legacy_home_disabled():
    result = ""
    image_url = ""
    business = ""
    company = ""
    style = ""

    if request.method == "POST":
        business = request.form.get("business", "").strip()
        company = request.form.get("company", "").strip()
        style = request.form.get("style", "").strip()

        if business and company and style:

            # 1. 광고 문구 생성
            result = make_ads(
                business,
                company,
                style,
                language=session.get("language", "ko")
            )

            # 2. 이미지 생성용 프롬프트
            image_prompt = f"""
            {company}의 광고용 이미지.

            업종: {business}
            브랜드 분위기: {style}

            전문적인 SNS 광고 사진 스타일.
            고급스럽고 자연스러운 실제 사진 느낌.
            깔끔한 구성.
            이미지 안에는 글자를 넣지 말 것.
            """

            # 3. AI 이미지 생성
            image_path = make_image(image_prompt)

            # Windows 경로 → 브라우저에서 사용할 URL
            image_url = "/" + image_path.replace("\\", "/")

            # 4. 히스토리 저장
            save_history(
                business,
                company,
                style,
                result,
                image_url
            )

            create_word(result)


            # Word 생성
            create_word(
                result,
                image_path
            )

            # PDF 생성
            create_pdf(
                result,
                image_path
            )

    # 중요!!
    # 이 return은 if request.method == "POST" 안에 들어가면 안 됨
    return render_template(
        "index.html",
        result=result,
        image_url=image_url,
        business=business,
        company=company,
        style=style
    )


# -------------------------
# 블로그 생성 페이지
# -------------------------

# -------------------------
# 생성 기록 페이지
# -------------------------

# -------------------------
# Word 다운로드
# -------------------------

@app.route("/download")
def download():
    if not os.path.exists(WORD_PATH):
        return "먼저 광고를 생성해 주세요.", 404

    return send_file(
        WORD_PATH,
        as_attachment=True,
        download_name="advertisement.docx"
    )

@app.route("/download/pdf")
def download_pdf():
    if not os.path.exists(PDF_PATH):
        return "먼저 광고를 생성해 주세요.", 404

    return send_file(
        PDF_PATH,
        as_attachment=True,
        download_name="advertisement.pdf"
    )


# -------------------------
# SNS 생성 페이지
# -------------------------


@app.route("/blog/download/word")
def download_blog_word():
    if not os.path.exists(BLOG_WORD_PATH):
        return "먼저 블로그 글을 생성해 주세요.", 404

    return send_file(
        BLOG_WORD_PATH,
        as_attachment=True,
        download_name="blog.docx"
    )


@app.route("/blog/download/pdf")
def download_blog_pdf():
    blog_pdf_path = "downloads/blog.pdf"

    if not os.path.exists(blog_pdf_path):
        return "먼저 블로그 글을 생성해 주세요.", 404

    return send_file(
        blog_pdf_path,
        as_attachment=True,
        download_name="blog.pdf"
    )

@app.route("/sns/download/word")
def download_sns_word():
    if not os.path.exists(SNS_WORD_PATH):
        return "먼저 SNS 글을 생성해 주세요.", 404

    return send_file(
        SNS_WORD_PATH,
        as_attachment=True,
        download_name="sns.docx"
    )


@app.route("/sns/download/pdf")
def download_sns_pdf():
    sns_pdf_path = "downloads/sns.pdf"

    if not os.path.exists(sns_pdf_path):
        return "먼저 SNS 글을 생성해 주세요.", 404

    return send_file(
        sns_pdf_path,
        as_attachment=True,
        download_name="sns.pdf"
    )


if __name__ == "__main__":
    # Listen on the local network too, so a phone on the same Wi-Fi can preview the app.
    app.run(host="0.0.0.0", port=5000, debug=True)
