from flask import Blueprint, render_template, request

from ai.blog import make_blog
from ai.image import make_image
from database.db import save_history
from database.users import get_ai_enabled
from documents.pdf import create_blog_pdf
from documents.word import create_blog_word
from routes.auth import login_required

blog_bp = Blueprint("blog", __name__)


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


@blog_bp.route("/blog", methods=["GET"])
def blog():
    return _blog_page()


@blog_bp.route("/blog", methods=["POST"])
@login_required
def generate_blog():
    return _blog_page()


def _blog_page():
    result = ""
    error = ""
    image_url = ""
    topic = ""
    tone = ""
    length = ""
    image_style = "고급스러운 실사"

    if request.method == "POST":
        if not get_ai_enabled():
            error = (
                "현재 AI 생성 시스템이 점검 중입니다. "
                "잠시 후 다시 이용해주세요."
            )

            return render_template(
                "blog.html",
                result=result,
                image_url=image_url,
                topic=topic,
                tone=tone,
                length=length,
                image_style=image_style,
                error=error
            )

        topic = request.form.get("topic", "").strip()
        tone = request.form.get("tone", "").strip()
        length = request.form.get("length", "").strip()
        image_style = request.form.get(
            "image_style",
            "고급스러운 실사"
        ).strip()

        if topic and tone and length:

            # 블로그 글 생성
            result = make_blog(
                topic,
                tone,
                length
            )

            # 대표 이미지 생성
            image_style_instruction = _image_style_instruction(
                image_style
            )

            image_prompt = f"""
블로그 대표 이미지.

주제: {topic}
분위기: {tone}
글의 길이: {length}
선택한 이미지 스타일: {image_style}
스타일 지시: {image_style_instruction}

블로그 주제와 실제 업종에 정확히 맞는 대표 이미지.
주제와 관계없는 마사지/스파 장면을 임의로 넣지 말 것.
깔끔하고 고급스러운 스타일.
본문 내용과 잘 어울리는 구성.
이미지 안에는 글자를 넣지 말 것.
"""

            image_path = ""

            try:
                image_path = make_image(image_prompt)
                image_url = "/" + image_path.replace("\\", "/")
            except Exception as image_error:
                print("블로그 이미지 생성 실패:", image_error)
                error = (
                    "블로그 글은 생성되었지만 이미지 생성에 실패했습니다. "
                    f"오류: {image_error}"
                )
                image_url = ""

            save_history(
                "BLOG",
                topic,
                tone,
                result,
                image_url
            )

            create_blog_word(
                result,
                image_path
            )

            create_blog_pdf(
                result,
                image_path
            )
    return render_template(
        "blog.html",
        result=result,
        image_url=image_url,
        topic=topic,
        tone=tone,
        length=length,
        image_style=image_style,
        error=error
    )