from flask import Blueprint, render_template, request

from ai.blog import make_blog
from ai.image import make_image
from database.db import save_history
from database.users import get_ai_enabled
from documents.pdf import create_blog_pdf
from documents.word import create_blog_word

blog_bp = Blueprint("blog", __name__)


@blog_bp.route("/blog", methods=["GET", "POST"])
def blog():
    result = ""
    error = ""
    image_url = ""
    topic = ""
    tone = ""
    length = ""

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
                error=error
            )

        topic = request.form.get("topic", "").strip()
        tone = request.form.get("tone", "").strip()
        length = request.form.get("length", "").strip()

        if topic and tone and length:

            # 블로그 글 생성
            result = make_blog(
                topic,
                tone,
                length
            )

            # 대표 이미지 생성
            image_prompt = f"""
블로그 대표 이미지.

주제: {topic}
분위기: {tone}
글의 길이: {length}

전문적이고 자연스러운 블로그 대표 이미지.
깔끔하고 고급스러운 스타일.
본문 내용과 잘 어울리는 구성.
이미지 안에는 글자를 넣지 말 것.
"""

            image_path = make_image(image_prompt)

            image_url = "/" + image_path.replace("\\", "/")

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
        error=error
    )