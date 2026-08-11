import gc
from pathlib import Path
import uuid

from PIL import Image, ImageDraw, ImageFont
import zipfile

from flask import Blueprint, render_template, request, send_file

from ai.ads import make_ads
from ai.blog import make_blog
from ai.sns import make_sns
from ai.image import make_image

from database.db import save_history
from database.profiles import get_profile

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



def _find_brand_font(size: int):
    candidates = [
        Path(r"C:\Windows\Fonts\malgunbd.ttf"),
        Path(r"C:\Windows\Fonts\malgun.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
    ]

    for font_path in candidates:
        if font_path.exists():
            try:
                return ImageFont.truetype(str(font_path), size=size)
            except Exception:
                pass

    return ImageFont.load_default()


def _add_company_name_to_image(image_path: str, company: str) -> str:
    """
    SNS 이미지 하단에 업체명을 프리미엄 스파 광고처럼 합성합니다.
    검은 박스 대신 은은한 하단 그라데이션 + 브랜드명 + 서브카피를 사용합니다.
    """
    if not image_path or not company:
        return image_path

    path = Path(image_path)

    if not path.exists():
        return image_path

    try:
        with Image.open(str(path)) as source:
            image = source.convert("RGBA")

        width, height = image.size

        # -------------------------------------------------
        # 하단 은은한 그라데이션
        # -------------------------------------------------
        overlay = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0)
        )

        overlay_draw = ImageDraw.Draw(
            overlay,
            "RGBA"
        )

        gradient_height = int(
            height * 0.30
        )

        gradient_start = (
            height
            - gradient_height
        )

        for step in range(
            gradient_height
        ):
            progress = (
                step
                / max(
                    1,
                    gradient_height - 1
                )
            )

            alpha = int(
                150
                * progress
            )

            y = (
                gradient_start
                + step
            )

            overlay_draw.line(
                (
                    0,
                    y,
                    width,
                    y
                ),
                fill=(
                    0,
                    0,
                    0,
                    alpha
                )
            )

        image = Image.alpha_composite(
            image,
            overlay
        )

        draw = ImageDraw.Draw(
            image,
            "RGBA"
        )

        # -------------------------------------------------
        # 브랜드명
        # -------------------------------------------------
        brand_font_size = max(
            24,
            int(
                width
                * 0.040
            )
        )

        brand_font = _find_brand_font(
            brand_font_size
        )

        max_text_width = (
            width
            * 0.78
        )

        while brand_font_size > 18:
            brand_bbox = draw.textbbox(
                (0, 0),
                company,
                font=brand_font
            )

            brand_width = (
                brand_bbox[2]
                - brand_bbox[0]
            )

            if brand_width <= max_text_width:
                break

            brand_font_size -= 2

            brand_font = _find_brand_font(
                brand_font_size
            )

        brand_bbox = draw.textbbox(
            (0, 0),
            company,
            font=brand_font
        )

        brand_width = (
            brand_bbox[2]
            - brand_bbox[0]
        )

        brand_height = (
            brand_bbox[3]
            - brand_bbox[1]
        )

        # -------------------------------------------------
        # 작은 서브카피
        # -------------------------------------------------
        tagline = (
            "RELAX · HEAL · REFRESH"
        )

        tagline_font_size = max(
            12,
            int(
                width
                * 0.018
            )
        )

        tagline_font = _find_brand_font(
            tagline_font_size
        )

        tagline_bbox = draw.textbbox(
            (0, 0),
            tagline,
            font=tagline_font
        )

        tagline_width = (
            tagline_bbox[2]
            - tagline_bbox[0]
        )

        tagline_height = (
            tagline_bbox[3]
            - tagline_bbox[1]
        )

        # -------------------------------------------------
        # 중앙 정렬 위치
        # -------------------------------------------------
        bottom_margin = int(
            height
            * 0.045
        )

        tagline_y = (
            height
            - bottom_margin
            - tagline_height
        )

        brand_y = (
            tagline_y
            - int(
                height
                * 0.012
            )
            - brand_height
        )

        brand_x = (
            width
            - brand_width
        ) // 2

        tagline_x = (
            width
            - tagline_width
        ) // 2

        # -------------------------------------------------
        # 은은한 그림자
        # -------------------------------------------------
        shadow_offset = max(
            1,
            int(
                width
                * 0.002
            )
        )

        draw.text(
            (
                brand_x
                + shadow_offset,
                brand_y
                + shadow_offset
            ),
            company,
            font=brand_font,
            fill=(
                0,
                0,
                0,
                150
            )
        )

        draw.text(
            (
                brand_x,
                brand_y
            ),
            company,
            font=brand_font,
            fill=(
                250,
                246,
                238,
                255
            )
        )

        draw.text(
            (
                tagline_x
                + shadow_offset,
                tagline_y
                + shadow_offset
            ),
            tagline,
            font=tagline_font,
            fill=(
                0,
                0,
                0,
                120
            )
        )

        draw.text(
            (
                tagline_x,
                tagline_y
            ),
            tagline,
            font=tagline_font,
            fill=(
                232,
                222,
                207,
                235
            )
        )

        # -------------------------------------------------
        # 저장
        # -------------------------------------------------
        suffix = path.suffix.lower()

        if suffix in [
            ".jpg",
            ".jpeg",
            ".webp"
        ]:
            image.convert("RGB").save(
                str(path),
                quality=94
            )
        else:
            image.save(
                str(path)
            )

        return str(path)

    except Exception as error:
        print(
            "SNS 업체명 합성 실패:",
            error
        )

        return image_path



def _is_fun_animal_style(image_style: str) -> bool:
    return image_style == "귀엽고 유머러스한 동물 콘셉트"


def _make_sns_image(company, business, sns_platform, style, image_style):
    if _is_fun_animal_style(image_style):
        primary_prompt = f"""
SNS 게시물용 재미있는 상업 이미지.

업종: {business}
플랫폼: {sns_platform}
브랜드 분위기: {style}

귀엽고 유머러스한 동물 캐릭터가 실제 사진처럼 보이는 광고 장면.
예: 선글라스를 쓴 고양이가 다른 고양이의 어깨나 등을
진지하게 마사지해 주는 모습처럼 한눈에 웃음이 나는 콘셉트.
동물은 의인화되어 있지만 전체 이미지는 고급 상업 사진처럼 세련되게 표현.
따뜻한 웰니스 공간, 포근한 조명, 깨끗한 인테리어.
밈처럼 재미있고 SNS에서 시선을 끌지만 저급하거나 과장된 만화 느낌은 피할 것.
이미지 안에는 글자, 로고, 워터마크를 넣지 말 것.
"""
    else:
        primary_prompt = f"""
SNS 게시물용 상업 이미지.

업종: {business}
플랫폼: {sns_platform}
브랜드 분위기: {style}
이미지 스타일: {image_style}

세련되고 전문적인 웰니스 또는 마사지 서비스 공간의 실제 광고 사진.
성인 고객은 단정한 서비스 의상으로 충분히 가려진 상태.
전문 테라피스트가 어깨 중심의 편안하고 건전한 웰니스 서비스를 제공하는 장면.
고객과 테라피스트 모두 자연스럽고 전문적인 자세.
따뜻한 조명, 정돈된 인테리어, 편안하고 고급스러운 분위기.
가족 친화적인 상업 광고 사진.
신체 노출이나 선정적인 연출 없이 표현.
이미지 안에는 글자, 로고, 워터마크를 넣지 말 것.
"""

    image_path, image_url = _make_image_safe(
        primary_prompt,
        "SNS 1차"
    )

    if not image_path:
        if _is_fun_animal_style(image_style):
            retry_prompt = f"""
Cute humorous premium social media advertising photo for a {business}.
Two adorable anthropomorphic cats in a luxury wellness studio.
One cat wears stylish sunglasses and gives the other cat a playful shoulder massage.
Warm lighting, polished commercial photography, charming and funny, family-friendly.
No text, no logo, no watermark.
"""
        else:
            retry_prompt = f"""
Professional commercial social media photo for a {business} business.
Brand mood: {style}. Visual style: {image_style}.
A clean elegant wellness interior with a professional therapist providing
a fully clothed adult client with a relaxing shoulder wellness service.
Warm lighting, polished interior, calm atmosphere, family-friendly advertising photography.
No nudity, no suggestive pose, no text, no logo, no watermark.
"""

        image_path, image_url = _make_image_safe(
            retry_prompt,
            "SNS 재시도"
        )

    if image_path:
        image_path = _add_company_name_to_image(
            image_path,
            company
        )

        image_url = "/" + str(
            Path(image_path)
        ).replace("\\", "/")

    return image_path, image_url


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
    loaded_profile_name = ""
    selected_profile_id = None

    # =====================================
    # GET: 저장된 브랜드 프로필 불러오기
    # =====================================

    if request.method == "GET":
        profile_id = request.args.get(
            "profile_id",
            type=int
        )

        selected_profile_id = profile_id

        if profile_id:
            profile = get_profile(
                profile_id
            )

            if profile:
                (
                    _profile_id,
                    business,
                    company,
                    style,
                    image_style,
                    sns_platform,
                    blog_length,
                    ads_count
                ) = profile

                loaded_profile_name = company

            else:
                error = "선택한 브랜드 프로필을 찾을 수 없습니다."

    # =====================================
    # POST: 마케팅 패키지 생성
    # =====================================

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

        selected_profile_id = request.form.get(
            "profile_id",
            type=int
        )

        if ads_count not in [3, 5, 10]:
            ads_count = 5

        if not all([business, company, style]):
            error = "업종, 회사명, 브랜드 분위기를 모두 입력해 주세요."

        else:
            try:
                # 광고/블로그/SNS 3개 기록을 한 패키지로 묶는 고유 ID
                package_id = uuid.uuid4().hex

                # =====================================
                # 1. 광고
                # =====================================

                ads_result = make_ads(
                    business,
                    company,
                    style,
                    ads_count
                )

                if _is_fun_animal_style(image_style):
                    ads_prompt = f"""
{company}의 재미있는 상업 광고 이미지.

업종: {business}
브랜드 분위기: {style}

귀엽고 유머러스한 동물들이 웰니스 서비스를 즐기는 장면.
선글라스를 쓴 고양이가 다른 고양이를 진지하게 마사지하는 것처럼
SNS에서 바로 시선을 끌 수 있는 재치 있는 콘셉트.
실제 고급 광고 사진처럼 디테일하고 자연스러운 털 표현.
따뜻하고 세련된 스파 인테리어, 가족 친화적이고 밝은 분위기.
글자, 로고, 워터마크는 넣지 말 것.
"""
                else:
                    ads_prompt = f"""
{company}의 상업용 광고 이미지.

업종: {business}
브랜드 분위기: {style}
이미지 스타일: {image_style}

고급스럽고 전문적인 마사지샵의 실제 서비스 장면.
성인 고객이 단정한 마사지복 또는 수건으로 충분히 가려진 상태에서
전문 마사지 테라피스트에게 어깨나 등 중심의 건전한 마사지를 받는 모습.
테라피스트와 고객 모두 자연스럽고 전문적인 자세.
신체 노출은 최소화하고 성적인 분위기는 전혀 없게 표현.
따뜻한 조명, 정돈된 인테리어, 편안한 웰니스 분위기.
상업 광고에 사용할 수 있는 가족 친화적이고 전문적인 사진.
이미지 안에는 글자를 넣지 말 것.
"""

                (
                    ads_image_path,
                    ads_image_url
                ) = _make_image_safe(
                    ads_prompt,
                    "광고"
                )

                if ads_image_path:
                    ads_image_path = _add_company_name_to_image(
                        ads_image_path,
                        company
                    )

                    ads_image_url = "/" + str(
                        Path(ads_image_path)
                    ).replace("\\", "/")

                save_history(
                    business,
                    company,
                    style,
                    ads_result,
                    ads_image_url,
                    content_type="ads",
                    package_id=package_id,
                    brand_profile_id=selected_profile_id
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

                if _is_fun_animal_style(image_style):
                    blog_prompt = f"""
블로그 대표 이미지.

주제: {blog_topic}
브랜드 분위기: {style}

귀엽고 유머러스한 동물 웰니스 콘셉트.
고양이 두 마리가 고급 마사지샵에서 마사지 테라피스트와 고객 역할을 하는 장면.
실제 사진처럼 섬세하고 고급스러우면서도 한눈에 재미있는 이미지.
선글라스나 작은 수건 같은 재치 있는 소품을 자연스럽게 사용.
따뜻한 조명, 고급 스파 인테리어, 가족 친화적인 분위기.
글자, 로고, 워터마크는 넣지 말 것.
"""
                else:
                    blog_prompt = f"""
블로그 대표 이미지.

주제: {blog_topic}
브랜드 분위기: {style}
이미지 스타일: {image_style}

고급스럽고 전문적인 마사지샵의 실제 서비스 장면.
성인 고객이 단정한 마사지복 또는 수건으로 충분히 가려진 상태에서
전문 마사지 테라피스트에게 어깨나 등 중심의 건전한 마사지를 받는 모습.
신체 노출은 최소화하고 성적인 분위기는 전혀 없게 표현.
깔끔하고 편안하며 블로그 대표 이미지에 적합한 자연스러운 구도.
따뜻한 조명과 전문적인 웰니스 공간.
이미지 안에는 글자를 넣지 말 것.
"""

                (
                    blog_image_path,
                    blog_image_url
                ) = _make_image_safe(
                    blog_prompt,
                    "블로그"
                )

                if blog_image_path:
                    blog_image_path = _add_company_name_to_image(
                        blog_image_path,
                        company
                    )

                    blog_image_url = "/" + str(
                        Path(blog_image_path)
                    ).replace("\\", "/")

                save_history(
                    business,
                    company,
                    style,
                    blog_result,
                    blog_image_url,
                    content_type="blog",
                    package_id=package_id,
                    brand_profile_id=selected_profile_id
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

                (
                    sns_image_path,
                    sns_image_url
                ) = _make_sns_image(
                    company,
                    business,
                    sns_platform,
                    style,
                    image_style
                )

                save_history(
                    business,
                    company,
                    style,
                    sns_result,
                    sns_image_url,
                    content_type="sns",
                    package_id=package_id,
                    brand_profile_id=selected_profile_id
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
        error=error,
        loaded_profile_name=loaded_profile_name,
        selected_profile_id=selected_profile_id
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
