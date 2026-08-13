from flask import Blueprint, render_template, request

from ai.sns import make_sns
from ai.image import make_image
from database.db import save_history
from database.users import get_ai_enabled
from documents.pdf import create_sns_pdf
from documents.word import create_sns_word

sns_bp = Blueprint("sns", __name__)


@sns_bp.route("/sns", methods=["GET", "POST"])
def sns():
    result = ""
    image_url = ""
    error = ""

    business = ""
    company = ""
    style = ""
    platform = ""

    if request.method == "POST":
        if not get_ai_enabled():
            error = (
                "현재 AI 생성 시스템이 점검 중입니다. "
                "잠시 후 다시 이용해주세요."
            )

            return render_template(
                "sns.html",
                result=result,
                image_url=image_url,
                error=error,
                business=business,
                company=company,
                style=style,
                platform=platform
            )

        business = request.form.get("business", "").strip()
        company = request.form.get("company", "").strip()
        style = request.form.get("style", "").strip()
        platform = request.form.get("platform", "").strip()

        if not all([business, company, style, platform]):
            error = "모든 항목을 입력해 주세요."

        else:
            try:
                # SNS 글 생성
                result = make_sns(
                    business,
                    company,
                    style,
                    platform
                )

                # SNS 이미지 생성
                image_prompt = f"""
SNS 게시물용 대표 이미지.

회사명: {company}
업종: {business}
플랫폼: {platform}
브랜드 분위기: {style}

전문적인 소셜미디어 광고 사진 스타일.
세련되고 시선을 끄는 구성.
브랜드 분위기에 어울리는 자연스럽고 고급스러운 이미지.
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

                create_sns_word(
                    result,
                    image_path
                )

                create_sns_pdf(
                    result,
                    image_path
                )

            except Exception as e:
                error = f"SNS 생성 오류: {e}"
                print(error)

    return render_template(
        "sns.html",
        result=result,
        image_url=image_url,
        error=error,
        business=business,
        company=company,
        style=style,
        platform=platform
    )