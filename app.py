import os
import sqlite3

from flask import Flask, render_template, request, send_file
from docx import Document

from ai.ads import make_ads
from ai.blog import make_blog


app = Flask(__name__)

DB_PATH = "project.db"
WORD_PATH = "downloads/advertisement.docx"


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

    conn.commit()
    conn.close()


def save_history(business, company, style, result):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO history (
            business,
            company,
            style,
            result
        )
        VALUES (?, ?, ?, ?)
    """, (
        business,
        company,
        style,
        result
    ))

    conn.commit()
    conn.close()


def get_history():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, business, company, style, result
        FROM history
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


# 프로그램 시작 시 DB 준비
init_db()


# -------------------------
# Word 문서
# -------------------------

def create_word(result):
    os.makedirs("downloads", exist_ok=True)

    document = Document()
    document.add_heading("Project Freedom AI", level=1)
    document.add_paragraph(result)
    document.save(WORD_PATH)

    return WORD_PATH


# -------------------------
# 광고 생성 페이지
# -------------------------

@app.route("/", methods=["GET", "POST"])
def home():
    result = ""
    business = ""
    company = ""
    style = ""

    if request.method == "POST":
        business = request.form.get("business", "").strip()
        company = request.form.get("company", "").strip()
        style = request.form.get("style", "").strip()

        if business and company and style:
            result = make_ads(
                business,
                company,
                style
            )

            save_history(
                business,
                company,
                style,
                result
            )

            create_word(result)

    return render_template(
        "index.html",
        result=result,
        business=business,
        company=company,
        style=style
    )


# -------------------------
# 블로그 생성 페이지
# -------------------------

@app.route("/blog", methods=["GET", "POST"])
def blog():
    result = ""
    topic = ""
    tone = ""
    length = ""

    if request.method == "POST":
        topic = request.form.get("topic", "").strip()
        tone = request.form.get("tone", "").strip()
        length = request.form.get("length", "").strip()

        if topic and tone and length:
            result = make_blog(
                topic,
                tone,
                length
            )

    return render_template(
        "blog.html",
        result=result,
        topic=topic,
        tone=tone,
        length=length
    )


# -------------------------
# 생성 기록 페이지
# -------------------------

@app.route("/history")
def history():
    history_list = get_history()

    return render_template(
        "history.html",
        history_list=history_list
    )


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


if __name__ == "__main__":
    app.run(debug=True)