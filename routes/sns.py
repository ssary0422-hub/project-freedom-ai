from flask import Blueprint, render_template, request

from ai.sns import make_sns
from ai.image import make_image
from database.db import save_history
from database.users import get_ai_enabled
from documents.pdf import create_sns_pdf
from documents.word import create_sns_word
from routes.auth import login_required

sns_bp = Blueprint("sns", __name__)


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


@sns_bp.route("/sns", methods=["GET"])
def sns():
    return _sns_page()


@sns_bp.route("/sns", methods=["POST"])
@login_required
def generate_sns():
    return _sns_page()


def _sns_page():
    result = ""
    image_url = ""
    error = ""

    business = ""
    company = ""
    style = ""
    platform = ""
    image_style = "고급스러운 실사"

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
                platform=platform,
                image_style=image_style
            )

        business = request.form.get("business", "").strip()
        company = request.form.get("company", "").strip()
        style = request.form.get("style", "").strip()
        platform = request.form.get("platform", "").strip()
        image_style = request.form.get(
            "image_style",
            "고급스러운 실사"
        ).strip()

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
                image_style_instruction = _image_style_instruction(
                    image_style
                )

                image_prompt = f"""
SNS 게시물용 대표 이미지.

회사명: {company}
업종: {business}
플랫폼: {platform}
브랜드 분위기: {style}
선택한 이미지 스타일: {image_style}
스타일 지시: {image_style_instruction}

업종과 회사명에 정확히 맞는 소셜미디어 광고 이미지.
마사지샵이 아닌 업종에는 마사지 장면이나 스파 소품을 임의로 넣지 말 것.
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
        platform=platform,
        image_style=image_style
    )