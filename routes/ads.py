import os

from flask import Blueprint, render_template, request, send_file

from ai.ads import make_ads
from ai.image import make_image
from documents.pdf import create_pdf, PDF_PATH
from database.db import save_history
from database.users import get_ai_enabled
from documents.word import create_word

ads_bp = Blueprint("ads", __name__)


@ads_bp.route("/", methods=["GET", "POST"])
def home():
    result = ""
    image_url = ""
    business = ""
    company = ""
    style = ""
    error = ""

    if request.method == "POST":
        if not get_ai_enabled():
            return render_template(
                "index.html",
                result=result,
                image_url=image_url,
                business=business,
                company=company,
                style=style,
                error=(
                    "현재 AI 생성 시스템이 점검 중입니다. "
                    "잠시 후 다시 이용해주세요."
                )
            )

        business = request.form.get("business", "").strip()
        company = request.form.get("company", "").strip()
        style = request.form.get("style", "").strip()

        if business and company and style:
            result = make_ads(
                business,
                company,
                style
            )

            image_prompt = f"""
{company}의 광고용 이미지.

업종: {business}
회사명: {company}
브랜드 분위기: {style}

전문적인 광고 이미지.
고급스럽고 자연스러운 실제 사진 느낌.
깔끔한 구성.
이미지 안에는 글자를 넣지 말 것.
"""

            image_path = make_image(image_prompt)

            image_url = "/" + image_path.replace("\\", "/")

            save_history(
                business,
                company,
                style,
                result,
                image_url
            )

            create_word(
                result,
                image_path
            )
            # DB 저장 / Word / PDF는
            # 다음 단계에서 별도 모듈로 연결

    return render_template(
        "index.html",
        result=result,
        image_url=image_url,
        business=business,
        company=company,
        style=style,
        error=error
    )


@ads_bp.route("/download/pdf")
def download_pdf():
    if not os.path.exists(PDF_PATH):
        return "먼저 광고를 생성해 주세요.", 404

    return send_file(
        PDF_PATH,
        as_attachment=True,
        download_name="advertisement.pdf"
    )