import os
import sqlite3

from routes.ads import ads_bp
from routes.blog import blog_bp
from routes.sns import sns_bp
from routes.history import history_bp
from database.db import init_db
from routes.package import package_bp
from routes.profiles import profiles_bp

from flask import (
    Flask,
    render_template,
    request,
    send_file,
    redirect
)
from docx import Document
from docx.shared import Inches
from documents.pdf import (
    create_pdf,
    create_blog_pdf,
    create_sns_pdf,
    PDF_PATH
)

from ai.ads import make_ads
from ai.blog import make_blog
from ai.sns import make_sns
from ai.image import make_image

app = Flask(__name__)

init_db()


app.register_blueprint(ads_bp)
app.register_blueprint(blog_bp)
app.register_blueprint(sns_bp)
app.register_blueprint(history_bp)
app.register_blueprint(package_bp)
app.register_blueprint(profiles_bp)

DB_PATH = "project.db"
WORD_PATH = "downloads/advertisement.docx"
BLOG_WORD_PATH = "downloads/blog.docx"
SNS_WORD_PATH = "downloads/sns.docx"

# -------------------------
# 데이터베이스
# -------------------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business TEXT,
            company TEXT,
            style TEXT,
            result TEXT
        )
    """)

    cursor.execute("PRAGMA table_info(history)")
    columns = [column[1] for column in cursor.fetchall()]

    if "image_url" not in columns:
        cursor.execute("""
            ALTER TABLE history
            ADD COLUMN image_url TEXT
        """)

    conn.commit()
    conn.close()


def save_history(business, company, style, result, image_url=""):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO history (
            business,
            company,
            style,
            result,
            image_url
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        business,
        company,
        style,
        result,
        image_url
    ))

    conn.commit()
    conn.close()


def get_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            business,
            company,
            style,
            result,
            image_url
        FROM history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows

@app.route("/delete/<int:id>")
def delete(id):

    delete_history(id)

    return redirect("/history")

    
def delete_history(id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM history WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()


# 프로그램 시작 시 DB 준비
init_db()


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

@app.route("/", methods=["GET", "POST"])
def home():
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
                style
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
    app.run(debug=True)