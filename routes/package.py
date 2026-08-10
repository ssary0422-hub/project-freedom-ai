import gc
from pathlib import Path
import zipfile

from flask import Blueprint, render_template, request, send_file

from ai.ads import make_ads
from ai.blog import make_blog
from ai.sns import make_sns
from ai.image import make_image

from database.db import save_history

from documents.word import (
    create_word,
    create_blog_word,
    create_sns_word,
    WORD_PATH,
    BLOG_WORD_PATH,
    SNS_WORD_PATH,
)

from documents.pdf import (
    create_pdf,
    create_blog_pdf,
    create_sns_pdf,
    PDF_PATH,
    BLOG_PDF_PATH,
    SNS_PDF_PATH,
)


package_bp = Blueprint("package", __name__)


BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

PACKAGE_ZIP_PATH = DOWNLOAD_DIR / "marketing_package.zip"


def _make_image_safe(prompt: str, label: str):
    try:
        image_path = make_image(prompt)
        image_path = str(Path(image_path))

        image_url = "/" + image_path.replace("\\", "/")

        return image_path, image_url

    except Exception as error:
        print(f"{label} 이미지 생성 실패:", error)

        return "", ""

    finally:
        gc.collect()


def _add_to_zip(zip_file, file_path, zip_name):
    if not file_path:
        return

    path = Path(file_path)

    if path.exists():
        zip_file.write(
            str(path),
            zip_name
        )


def _image_zip_name(image_path: str, base_name: str) -> str:
    if not image_path:
        return f"images/{base_name}.jpg"

    suffix = Path(image_path).suffix.lower()

    if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
        suffix = ".jpg"

    return f"images/{base_name}{suffix}"


def create_package_zip(
    ads_image_path: str,
    blog_image_path: str,
    sns_image_path: str
) -> str:
    DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with zipfile.ZipFile(
        str(PACKAGE_ZIP_PATH),
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6
    ) as zip_file:

        # Word 3개
        _add_to_zip(
            zip_file,
            WORD_PATH,
            "advertisement.docx"
        )

        _add_to_zip(
            zip_file,
            BLOG_WORD_PATH,
            "blog.docx"
        )

        _add_to_zip(
            zip_file,
            SNS_WORD_PATH,
            "sns.docx"
        )

        # PDF 3개
        _add_to_zip(
            zip_file,
            PDF_PATH,
            "advertisement.pdf"
        )

        _add_to_zip(
            zip_file,
            BLOG_PDF_PATH,
            "blog.pdf"
        )

        _add_to_zip(
            zip_file,
            SNS_PDF_PATH,
            "sns.pdf"
        )

        # 이미지 3개
        _add_to_zip(
            zip_file,
            ads_image_path,
            _image_zip_name(
                ads_image_path,
                "advertisement"
            )
        )

        _add_to_zip(
            zip_file,
            blog_image_path,
            _image_zip_name(
                blog_image_path,
                "blog"
            )
        )

        _add_to_zip(
            zip_file,
            sns_image_path,
            _image_zip_name(
                sns_image_path,
                "sns"
            )
        )

    gc.collect()

    return str(PACKAGE_ZIP_PATH)


@package_bp.route("/package", methods=["GET", "POST"])
def package():
    business = ""
    company = ""
    style = ""

    blog_length = "2000자"
    sns_platform = "인스타그램"
    image_style = "고급스러운 실사"
    ads_count = 5

    ads_result = ""
    blog_result = ""
    sns_result = ""

    ads_image_url = ""
    blog_image_url = ""
    sns_image_url = ""

    package_ready = False
    error = ""

    if request.method == "POST":
        business = request.form.get(
            "business",
            ""
        ).strip()

        company = request.form.get(
            "company",
            ""
        ).strip()

        style = request.form.get(
            "style",
            ""
        ).strip()

        blog_length = request.form.get(
            "blog_length",
            "2000자"
        )

        sns_platform = request.form.get(
            "sns_platform",
            "인스타그램"
        )

        image_style = request.form.get(
            "image_style",
            "고급스러운 실사"
        )

        ads_count = request.form.get(
            "ads_count",
            5,
            type=int
        )

        if ads_count not in [3, 5, 10]:
            ads_count = 5

        if not all([business, company, style]):
            error = "업종, 회사명, 브랜드 분위기를 모두 입력해 주세요."

        else:
            try:
                # =====================================
                # 1. 광고
                # =====================================

                ads_result = make_ads(
                    business,
                    company,
                    style,
                    ads_count
                )

                ads_prompt = f"""
{company}의 상업용 광고 이미지.

업종: {business}
브랜드 분위기: {style}
이미지 스타일: {image_style}

깨끗하고 전문적인 상업용 웰니스 공간.
정돈된 인테리어와 편안한 분위기.
사람의 신체 노출이나 마사지 장면은 포함하지 말 것.
비성적이고 가족 친화적인 광고 이미지.
이미지 안에는 글자를 넣지 말 것.
"""

                (
                    ads_image_path,
                    ads_image_url
                ) = _make_image_safe(
                    ads_prompt,
                    "광고"
                )

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

                gc.collect()

                # =====================================
                # 2. 블로그
                # =====================================

                blog_topic = (
                    f"{company} {business} 소개와 "
                    f"이용할 때 알아두면 좋은 점"
                )

                blog_result = make_blog(
                    blog_topic,
                    style,
                    blog_length
                )

                blog_prompt = f"""
블로그 대표 이미지.

주제: {blog_topic}
브랜드 분위기: {style}
이미지 스타일: {image_style}

전문적인 상업용 웰니스 공간 이미지.
깔끔하고 편안하며 블로그 대표 이미지에 적합한 구성.
사람의 신체 노출이나 마사지 장면은 포함하지 말 것.
비성적이고 가족 친화적인 이미지.
이미지 안에는 글자를 넣지 말 것.
"""

                (
                    blog_image_path,
                    blog_image_url
                ) = _make_image_safe(
                    blog_prompt,
                    "블로그"
                )

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

                gc.collect()

                # =====================================
                # 3. SNS
                # =====================================

                sns_result = make_sns(
                    business,
                    company,
                    style,
                    sns_platform
                )

                sns_prompt = f"""
SNS 게시물용 상업 이미지.

회사명: {company}
업종: {business}
플랫폼: {sns_platform}
브랜드 분위기: {style}
이미지 스타일: {image_style}

세련되고 시선을 끄는 상업용 웰니스 공간.
SNS에 적합한 깔끔하고 전문적인 구성.
사람의 신체 노출이나 마사지 장면은 포함하지 말 것.
비성적이고 가족 친화적인 이미지.
이미지 안에는 글자를 넣지 말 것.
"""

                (
                    sns_image_path,
                    sns_image_url
                ) = _make_image_safe(
                    sns_prompt,
                    "SNS"
                )

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

                gc.collect()

                # =====================================
                # 4. ZIP
                # =====================================

                create_package_zip(
                    ads_image_path,
                    blog_image_path,
                    sns_image_path
                )

                package_ready = True

            except Exception as exc:
                error = f"패키지 생성 중 오류가 발생했습니다: {exc}"
                print("패키지 생성 오류:", repr(exc))

            finally:
                gc.collect()

    return render_template(
        "package.html",
        business=business,
        company=company,
        style=style,
        blog_length=blog_length,
        sns_platform=sns_platform,
        image_style=image_style,
        ads_count=ads_count,

        ads_result=ads_result,
        blog_result=blog_result,
        sns_result=sns_result,

        ads_image_url=ads_image_url,
        blog_image_url=blog_image_url,
        sns_image_url=sns_image_url,

        package_ready=package_ready,
        error=error
    )


@package_bp.route("/package/download")
def download_package():
    if not PACKAGE_ZIP_PATH.exists():
        return "먼저 마케팅 패키지를 생성해 주세요.", 404

    return send_file(
        str(PACKAGE_ZIP_PATH),
        as_attachment=True,
        download_name="marketing_package.zip"
    )
