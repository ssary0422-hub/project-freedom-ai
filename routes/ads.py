import os

from flask import Blueprint, render_template, request, send_file

from ai.ads import make_ads
from ai.image import make_image
from documents.pdf import create_pdf, PDF_PATH
from database.db import save_history
from database.users import get_ai_enabled
from documents.word import create_word
from routes.auth import login_required

ads_bp = Blueprint("ads", __name__)


def _image_style_instruction(image_style):
    style_map = {
        "고급스러운 실사": (
            "고급 상업용 실사 사진. 현실적인 조명, 세련된 구도, 프리미엄 광고 품질."
        ),
        "감성적인 분위기": (
            "따뜻하고 감성적인 라이프스타일 사진. 부드러운 조명과 자연스러운 분위기."
        ),
        "고양이 유머 콘셉트": (
            "귀엽고 유머러스한 고양이를 활용한 광고 콘셉트. 업종의 핵심 요소가 분명히 보여야 함."
        ),
        "강아지 유머 콘셉트": (
            "귀엽고 유머러스한 강아지를 활용한 광고 콘셉트. 업종의 핵심 요소가 분명히 보여야 함."
        ),
        "코끼리 유머 콘셉트": (
            "친근하고 유쾌한 코끼리를 활용한 광고 콘셉트. 업종의 핵심 요소가 분명히 보여야 함."
        ),
        "랜덤 동물 유머 콘셉트": (
            "업종에 어울리는 동물 한 종류를 선택한 유머러스한 광고 콘셉트."
        ),
        "미니멀하고 깔끔한 스타일": (
            "미니멀하고 깔끔한 상업 비주얼. 단정한 배경, 절제된 소품, 명확한 주제."
        ),
        "화려한 광고 비주얼": (
            "시선을 강하게 끄는 화려한 광고 비주얼. 역동적인 구도와 풍부한 디테일."
        ),
    }

    return style_map.get(
        image_style,
        style_map["고급스러운 실사"]
    )


@ads_bp.route("/", methods=["GET"])
def home():
    return _home_page()


@ads_bp.route("/", methods=["POST"])
@login_required
def generate_ads():
    return _home_page()


def _home_page():
    result = ""
    image_url = ""
    business = ""
    company = ""
    style = ""
    image_style = "고급스러운 실사"
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
                image_style=image_style,
                error=(
                    "현재 AI 생성 시스템이 점검 중입니다. "
                    "잠시 후 다시 이용해주세요."
                )
            )

        business = request.form.get("business", "").strip()
        company = request.form.get("company", "").strip()
        style = request.form.get("style", "").strip()
        image_style = request.form.get(
            "image_style",
            "고급스러운 실사"
        ).strip()

        if business and company and style:
            result = make_ads(
                business,
                company,
                style
            )

            image_style_instruction = _image_style_instruction(
                image_style
            )

            image_prompt = f"""
{company}의 광고용 이미지.

업종: {business}
회사명: {company}
브랜드 분위기: {style}
선택한 이미지 스타일: {image_style}
스타일 지시: {image_style_instruction}

업종과 회사명에 정확히 맞는 전문적인 광고 이미지.
마사지샵이 아닌 업종에는 마사지 베드, 마사지 장면, 스파 소품을 넣지 말 것.
병원/의원은 의료진, 진료 공간, 의료 장비 등 해당 진료 업종에 맞게 표현할 것.
카페는 카페 공간, 음료, 디저트 등 카페 업종에 맞게 표현할 것.
고급스럽고 자연스러운 실제 사진 느낌.
깔끔한 구성.
이미지 안에는 글자를 넣지 말 것.
"""

            image_path = ""

            try:
                image_path = make_image(image_prompt)
                image_url = "/" + image_path.replace("\\", "/")
            except Exception as image_error:
                print("광고 이미지 생성 실패:", image_error)
                error = (
                    "광고 문구는 생성되었지만 이미지 생성에 실패했습니다. "
                    f"오류: {image_error}"
                )
                image_url = ""

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

            create_pdf(
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
        image_style=image_style,
        error=error
    )


@ads_bp.route("/download/pdf")
@login_required
def download_pdf():
    if not os.path.exists(PDF_PATH):
        return "먼저 광고를 생성해 주세요.", 404

    return send_file(
        PDF_PATH,
        as_attachment=True,
        download_name="advertisement.pdf"
    )