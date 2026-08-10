import os
import zipfile

from flask import (
    Blueprint,
    render_template,
    request,
    send_file
)

from flask import Blueprint, render_template, request

from ai.ads import make_ads
from ai.blog import make_blog
from ai.sns import make_sns
from ai.image import make_image

from database.db import save_history

from documents.word import (
    create_word,
    create_blog_word,
    create_sns_word,
)

from documents.pdf import (
    create_pdf,
    create_blog_pdf,
    create_sns_pdf,
)


package_bp = Blueprint("package", __name__)


@package_bp.route("/package", methods=["GET", "POST"])
def package():
    business = ""
    company = ""
    style = ""

    ads_result = ""
    blog_result = ""
    sns_result = ""

    ads_image_url = ""
    blog_image_url = ""
    sns_image_url = ""

    if request.method == "POST":
        business = request.form.get("business", "").strip()
        company = request.form.get("company", "").strip()
        style = request.form.get("style", "").strip()

        if business and company and style:

            # -------------------------
            # 1. 광고
            # -------------------------

            ads_result = make_ads(
                business,
                company,
                style
            )

            ads_prompt = f"""
{company}의 광고용 이미지.

업종: {business}
분위기: {style}

전문적인 광고 사진.
고급스럽고 자연스러운 실제 사진 느낌.
이미지 안에는 글자를 넣지 말 것.
"""

            ads_image_path = make_image(
                ads_prompt
            )

            ads_image_url = "/" + ads_image_path.replace("\\", "/")

            save_history(
                business,
                company,
                style,
                ads_result,
                ads_image_url
            )

            create_word(
                ads_result,
                ads_image_path
            )

            create_pdf(
                ads_result,
                ads_image_path
            )

            # -------------------------
            # 2. 블로그
            # -------------------------

            blog_topic = (
                f"{company} {business} 소개와 "
                f"이용할 때 알아두면 좋은 점"
            )

            blog_tone = style
            blog_length = "2000자"

            blog_result = make_blog(
                blog_topic,
                blog_tone,
                blog_length
            )

            blog_prompt = f"""
블로그 대표 이미지.

주제: {blog_topic}
분위기: {style}

전문적이고 자연스러운 블로그 대표 이미지.
깔끔하고 고급스러운 스타일.
이미지 안에는 글자를 넣지 말 것.
"""

            blog_image_path = make_image(
                blog_prompt
            )

            blog_image_url = "/" + blog_image_path.replace("\\", "/")

            save_history(
                "BLOG",
                blog_topic,
                style,
                blog_result,
                blog_image_url
            )

            create_blog_word(
                blog_result,
                blog_image_path
            )

            create_blog_pdf(
                blog_result,
                blog_image_path
            )

            # -------------------------
            # 3. SNS
            # -------------------------

            sns_platform = "인스타그램"

            sns_result = make_sns(
                business,
                company,
                style,
                sns_platform
            )

            sns_prompt = f"""
SNS 게시물용 대표 이미지.

회사명: {company}
업종: {business}
플랫폼: {sns_platform}
분위기: {style}

세련되고 시선을 끄는 SNS 광고 이미지.
자연스럽고 고급스러운 실제 사진 스타일.
이미지 안에는 글자를 넣지 말 것.
"""

            sns_image_path = make_image(
                sns_prompt
            )

            sns_image_url = "/" + sns_image_path.replace("\\", "/")

            save_history(
                business,
                company,
                style,
                sns_result,
                sns_image_url
            )

            create_sns_word(
                sns_result,
                sns_image_path
            )

            create_sns_pdf(
                sns_result,
                sns_image_path
            )

            create_package_zip(
                ads_image_path,
                blog_image_path,
                sns_image_path
            )

    return render_template(
        "package.html",
        business=business,
        company=company,
        style=style,
        ads_result=ads_result,
        blog_result=blog_result,
        sns_result=sns_result,
        ads_image_url=ads_image_url,
        blog_image_url=blog_image_url,
        sns_image_url=sns_image_url
    )

def create_package_zip(
    ads_image_path,
    blog_image_path,
    sns_image_path
):
    os.makedirs("downloads", exist_ok=True)

    zip_path = os.path.join(
        "downloads",
        "marketing_package.zip"
    )

    files = [
        (
            os.path.join("downloads", "advertisement.docx"),
            "advertisement.docx"
        ),
        (
            os.path.join("downloads", "advertisement.pdf"),
            "advertisement.pdf"
        ),
        (
            os.path.join("downloads", "blog.docx"),
            "blog.docx"
        ),
        (
            os.path.join("downloads", "blog.pdf"),
            "blog.pdf"
        ),
        (
            os.path.join("downloads", "sns.docx"),
            "sns.docx"
        ),
        (
            os.path.join("downloads", "sns.pdf"),
            "sns.pdf"
        ),
        (
            ads_image_path,
            "images/advertisement.png"
        ),
        (
            blog_image_path,
            "images/blog.png"
        ),
        (
            sns_image_path,
            "images/sns.png"
        )
    ]

    with zipfile.ZipFile(
        zip_path,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zip_file:

        for file_path, zip_name in files:

            if os.path.exists(file_path):
                zip_file.write(
                    file_path,
                    zip_name
                )

    return zip_path
    
@package_bp.route("/package/download")
def download_package():

    zip_path = os.path.join(
        "downloads",
        "marketing_package.zip"
    )

    if not os.path.exists(zip_path):
        return "먼저 마케팅 패키지를 생성해 주세요.", 404

    return send_file(
        zip_path,
        as_attachment=True,
        download_name="marketing_package.zip"
    )