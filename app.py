import sqlite3
import os
from flask import Flask, render_template, request, send_file
from openai import OpenAI
from docx import Document

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def init_db():

    conn = sqlite3.connect("project.db")

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


init_db()
# Word 파일 생성 함수
def create_word(result):
    os.makedirs("downloads", exist_ok=True)

    filename = "downloads/advertisement.docx"

    document = Document()
    document.add_heading("Project Freedom AI", level=1)
    document.add_paragraph(result)
    document.save(filename)

    return filename


# 메인 페이지
@app.route("/", methods=["GET", "POST"])
def home():

    result = ""
    business = ""
    company = ""
    style = ""

    if request.method == "POST":

        business = request.form["business"]
        company = request.form["company"]
        style = request.form["style"]

        prompt = f"""
업종 : {business}
회사명 : {company}
분위기 : {style}

SNS 광고 문구를 5개 만들어줘.
"""

        response = client.responses.create(
            model="gpt-5.5",
            input=prompt
        )

        result = response.output_text

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


# Word 다운로드
@app.route("/download")
def download():

    filename = "downloads/advertisement.docx"

    return send_file(
        filename,
        as_attachment=True
    )

def save_history(business, company, style, result):

    conn = sqlite3.connect("project.db")

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO history
        (business, company, style, result)
        VALUES (?, ?, ?, ?)
    """, (business, company, style, result))

    conn.commit()
    conn.close()

    if __name__ == "__main__":
        app.run(debug=True)