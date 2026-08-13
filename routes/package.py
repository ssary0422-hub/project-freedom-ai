import gc
from pathlib import Path
import uuid

from PIL import Image, ImageDraw, ImageFont
import zipfile

from flask import Blueprint, render_template, request, send_file, session, g

from ai.ads import make_ads
from ai.blog import make_blog
from ai.sns import make_sns
from ai.image import make_image

from database.db import save_history
from database.profiles import get_profile, get_profiles
from database.users import get_plan_status, record_package_usage, get_ai_enabled
from routes.auth import login_required

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
    if not getattr(g, "generate_images", True):
        return "", ""

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


def _brand_tagline_for_business(business: str) -> str:
    """
    업종에 맞는 짧은 영문 브랜드 슬로건을 반환합니다.
    """
    name = (business or "").strip().lower()

    rules = [
        (
            [
                "마사지",
                "마사지샵",
                "마사지숍",
                "스파",
                "spa",
                "아로마",
                "테라피",
            ],
            "RELAX · HEAL · REFRESH",
        ),
        (
            [
                "정형외과",
                "병원",
                "의원",
                "클리닉",
                "hospital",
                "clinic",
                "재활",
            ],
            "CARE · RECOVERY · WELLNESS",
        ),
        (
            [
                "피부과",
                "피부",
                "derma",
                "dermatology",
            ],
            "SKIN · BEAUTY · CONFIDENCE",
        ),
        (
            [
                "치과",
                "dental",
                "dentist",
            ],
            "SMILE · CARE · TRUST",
        ),
        (
            [
                "카페",
                "coffee",
                "cafe",
                "베이커리",
                "디저트",
            ],
            "COFFEE · MOMENT · RELAX",
        ),
        (
            [
                "음식점",
                "식당",
                "레스토랑",
                "restaurant",
                "고기집",
                "한식",
                "중식",
                "일식",
                "양식",
            ],
            "TASTE · ENJOY · TOGETHER",
        ),
        (
            [
                "미용실",
                "헤어",
                "hair",
                "salon",
                "네일",
                "nail",
                "뷰티",
                "beauty",
            ],
            "STYLE · BEAUTY · CONFIDENCE",
        ),
        (
            [
                "헬스",
                "헬스장",
                "fitness",
                "gym",
                "필라테스",
                "요가",
                "pt",
            ],
            "TRAIN · STRONG · CHANGE",
        ),
        (
            [
                "학원",
                "교육",
                "academy",
                "school",
                "영어",
                "수학",
            ],
            "LEARN · GROW · ACHIEVE",
        ),
        (
            [
                "부동산",
                "real estate",
                "공인중개",
            ],
            "TRUST · VALUE · HOME",
        ),
        (
            [
                "자동차",
                "세차",
                "카센터",
                "정비",
                "car",
                "auto",
            ],
            "DRIVE · CARE · CONFIDENCE",
        ),
    ]

    for keywords, tagline in rules:
        if any(
            keyword in name
            for keyword in keywords
        ):
            return tagline

    return "QUALITY · TRUST · EXPERIENCE"


def _add_company_name_to_image(image_path: str, company: str, business: str = "") -> str:
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
        tagline = _brand_tagline_for_business(
            business
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



ANIMAL_STYLE_MAP = {
    "고양이 유머 콘셉트": "cat",
    "강아지 유머 콘셉트": "dog",
    "코끼리 유머 콘셉트": "elephant",
    "랜덤 동물 유머 콘셉트": "random",
    # 이전에 저장된 브랜드 프로필과의 호환성 유지
    "귀엽고 유머러스한 동물 콘셉트": "cat",
}


def _animal_for_style(image_style: str) -> str:
    animal = ANIMAL_STYLE_MAP.get(
        image_style,
        ""
    )

    if animal != "random":
        return animal

    import random

    return random.choice([
        "cat",
        "dog",
        "elephant"
    ])


def _is_fun_animal_style(image_style: str) -> bool:
    return image_style in ANIMAL_STYLE_MAP


def _animal_prompt_name(image_style: str) -> str:
    animal = _animal_for_style(
        image_style
    )

    return {
        "cat": "adorable cats",
        "dog": "adorable dogs",
        "elephant": "adorable elephants",
    }.get(
        animal,
        "adorable animals"
    )


def _make_sns_image(company, business, sns_platform, style, image_style):
    if _is_fun_animal_style(image_style):
        primary_prompt = f"""
SNS 게시물용 재미있는 상업 이미지.

회사명: {company}
업종: {business}
플랫폼: {sns_platform}
브랜드 분위기: {style}
선택 동물: {_animal_prompt_name(image_style)}

반드시 '{business}' 업종을 한눈에 알아볼 수 있는 장면을 만들 것.
선택 동물 두 마리를 귀엽고 자연스럽게 의인화하여,
한 마리는 해당 업종의 전문 직원 역할, 다른 한 마리는 고객 역할을 하게 표현.
업종이 병원/의원/정형외과라면 진료실, 의료진 가운, 상담 또는 검사 장면처럼
의료기관임이 분명하게 보이게 하고 마사지, 스파, 테라피 장면은 절대 사용하지 말 것.
다른 업종도 반드시 그 업종의 실제 서비스 환경과 도구를 사용할 것.
고급 상업 사진처럼 사실적이고 세련되며 가족 친화적으로 표현.
이미지 안에는 글자, 로고, 워터마크를 넣지 말 것.
"""
    else:
        primary_prompt = f"""
SNS 게시물용 상업 이미지.

회사명: {company}
업종: {business}
플랫폼: {sns_platform}
브랜드 분위기: {style}
이미지 스타일: {image_style}

반드시 '{business}' 업종과 직접 관련된 실제 서비스 현장을 표현할 것.
업종이 병원/의원/정형외과라면 깨끗한 진료실, 전문 의료진,
환자 상담·진찰·검사 같은 신뢰감 있는 의료 장면을 표현하고
마사지샵, 스파, 웰니스 테라피 장면은 절대 사용하지 말 것.
다른 업종이라면 해당 업종의 공간, 직원, 고객, 핵심 서비스나 제품이
한눈에 이해되도록 정확하게 표현할 것.
브랜드 분위기 '{style}'에 맞는 조명과 인테리어.
전문적이고 자연스러운 상업 광고 사진.
이미지 안에는 글자, 로고, 워터마크를 넣지 말 것.
"""

    image_path, image_url = _make_image_safe(
        primary_prompt,
        "SNS 1차"
    )

    if not image_path:
        retry_prompt = f"""
Professional commercial advertising photo for this exact business category: {business}.
Company: {company}. Brand mood: {style}. Visual style: {image_style}.
The scene must unmistakably represent the real business category and its normal service environment.
If this is a hospital, clinic, orthopedic clinic, or medical business, show a clean medical consultation
or examination scene with professional medical staff and absolutely no massage, spa, or wellness treatment.
For any other business, show the correct workplace, staff, customer, products or services for that category.
Polished, realistic, family-friendly commercial photography.
No text, no logo, no watermark.
"""

        image_path, image_url = _make_image_safe(
            retry_prompt,
            "SNS 재시도"
        )

    if image_path:
        image_path = _add_company_name_to_image(
            image_path,
            company,
            business
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
@login_required
def package():
    business = ""
    company = ""
    style = ""

    blog_length = "2000자"
    sns_platform = "인스타그램"
    image_style = "고급스러운 실사"
    with_image = False
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

    plan_status = get_plan_status(
        session["user_id"]
    )
    plan = plan_status["plan"]

    # 로그인한 사용자의 저장된 브랜드 목록
    saved_profiles = get_profiles(
        session["user_id"]
    )

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
                profile_id,
                session["user_id"]
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
        if not get_ai_enabled():
            error = (
                "현재 AI 생성 시스템이 점검 중입니다. "
                "잠시 후 다시 이용해주세요."
            )

            return render_template(
                "package.html",
                business=business,
                company=company,
                style=style,
                blog_length=blog_length,
                sns_platform=sns_platform,
                image_style=image_style,
                with_image=with_image,
                ads_count=ads_count,
                ads_result=ads_result,
                blog_result=blog_result,
                sns_result=sns_result,
                ads_image_url=ads_image_url,
                blog_image_url=blog_image_url,
                sns_image_url=sns_image_url,
                package_ready=False,
                error=error,
                loaded_profile_name=loaded_profile_name,
                selected_profile_id=selected_profile_id,
                saved_profiles=saved_profiles,
                plan=plan
            )

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

        with_image = request.form.get("with_image") == "on"
        package_cost = 7 if with_image else 3

        plan_status = get_plan_status(
            session["user_id"],
            required_credits=package_cost
        )
        plan = plan_status["plan"]

        if not plan_status["can_generate"]:
            error = (
                f"{plan_status['plan']} 요금제의 AI 크레딧이 부족합니다. "
                f"현재 {plan_status['remaining']}크레딧 남음 · "
                f"이번 마케팅 패키지는 {package_cost}크레딧이 필요합니다."
            )
            return render_template(
                "package.html",
                business=business,
                company=company,
                style=style,
                blog_length=blog_length,
                sns_platform=sns_platform,
                image_style=image_style,
                with_image=with_image,
                ads_count=ads_count,
                ads_result=ads_result,
                blog_result=blog_result,
                sns_result=sns_result,
                ads_image_url=ads_image_url,
                blog_image_url=blog_image_url,
                sns_image_url=sns_image_url,
                package_ready=False,
                error=error,
                loaded_profile_name=loaded_profile_name,
                selected_profile_id=selected_profile_id,
                saved_profiles=saved_profiles,
                plan=plan
            )

        g.generate_images = with_image

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
선택 동물: {_animal_prompt_name(image_style)}

반드시 '{business}' 업종을 정확하게 표현할 것.
선택 동물 두 마리를 귀엽게 의인화해 한 마리는 해당 업종의 전문 직원,
다른 한 마리는 고객 역할로 표현.
병원/의원/정형외과라면 의료진 가운, 깨끗한 진료실, 상담·진찰·검사 장면을 사용하고
마사지, 스파, 테라피 장면은 절대 넣지 말 것.
다른 업종도 해당 업종의 실제 공간, 도구, 서비스가 명확히 보이게 할 것.
고급 상업 광고 사진처럼 사실적이고 세련되며 가족 친화적인 이미지.
글자, 로고, 워터마크는 넣지 말 것.
"""
                else:
                    ads_prompt = f"""
{company}의 상업용 광고 이미지.

업종: {business}
브랜드 분위기: {style}
이미지 스타일: {image_style}

반드시 '{business}' 업종의 실제 서비스 현장을 정확하게 표현할 것.
병원/의원/정형외과라면 깨끗한 진료실, 전문 의료진,
X-ray/MRI 영상, 관절 또는 척추 모형을 활용한 상담·진찰·검사 장면을 우선적으로 표현할 것.
의료진이 환자의 어깨나 등을 손으로 주무르거나 누르는 장면,
마사지·도수치료처럼 보일 수 있는 직접적인 신체 압박 장면,
마사지샵·스파·웰니스 테라피 장면은 절대 넣지 말 것.
다른 업종이라면 해당 업종의 공간, 직원, 고객, 핵심 서비스 또는 제품이
한눈에 이해되도록 표현할 것.
'{style}' 분위기의 전문적이고 자연스러운 상업 광고 사진.
이미지 안에는 글자를 넣지 말 것.
"""
                (
                    ads_image_path,
                    ads_image_url
                ) = _make_image_safe(
                    ads_prompt,
                    "광고"
                )

                if not ads_image_path:
                    ads_retry_prompt = f"""
Professional commercial advertising photo for {company}.
Exact business category: {business}.
Brand mood: {style}. Visual style: {image_style}.
Show the authentic workplace, professional staff, customer, and core service of this exact business.
For hospitals or clinics, show a clean medical consultation or examination scene,
preferably with X-ray/MRI images or an orthopedic joint/spine model.
Do not show the clinician pressing, rubbing, or massaging the patient's shoulders or back.
No massage, spa, manual therapy-looking treatment, or wellness treatment.
No text, no logo, no watermark.
"""
                    (
                        ads_image_path,
                        ads_image_url
                    ) = _make_image_safe(
                        ads_retry_prompt,
                        "광고 재시도"
                    )

                if ads_image_path:
                    ads_image_path = _add_company_name_to_image(
                        ads_image_path,
                        company,
                        business
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
                    brand_profile_id=selected_profile_id,
                    user_id=session["user_id"]
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

회사명: {company}
주제: {blog_topic}
업종: {business}
브랜드 분위기: {style}
선택 동물: {_animal_prompt_name(image_style)}

반드시 '{business}' 업종이 한눈에 보이는 블로그 대표 이미지를 만들 것.
선택 동물을 해당 업종의 직원과 고객 역할로 귀엽게 의인화하되,
병원/의원/정형외과라면 진료실, 의료진 가운, 상담·진찰·검사 장면으로 표현하고
마사지, 스파, 테라피 장면은 절대 사용하지 말 것.
다른 업종도 해당 업종의 실제 환경과 핵심 서비스를 정확하게 반영할 것.
사실적이고 고급스러운 상업 사진, 깔끔한 블로그 썸네일 구도.
글자, 로고, 워터마크는 넣지 말 것.
"""
                else:
                    blog_prompt = f"""
블로그 대표 이미지.

회사명: {company}
주제: {blog_topic}
업종: {business}
브랜드 분위기: {style}
이미지 스타일: {image_style}

반드시 '{business}' 업종의 실제 환경과 핵심 서비스를 정확하게 표현할 것.
병원/의원/정형외과라면 깨끗한 진료실, 전문 의료진,
환자 상담·진찰·검사 같은 의료 장면을 표현하고
마사지샵, 스파, 웰니스 테라피 장면은 절대 사용하지 말 것.
다른 업종이라면 해당 업종의 공간, 직원, 고객, 제품 또는 서비스를 명확히 표현할 것.
'{style}' 분위기의 자연스럽고 전문적인 블로그 대표 사진.
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
                        company,
                        business
                    )

                    blog_image_url = "/" + str(
                        Path(blog_image_path)
                    ).replace("\\", "/")

                if not blog_image_path:
                    blog_retry_prompt = f"""
Professional blog hero image for {company}.
Exact business category: {business}.
Topic: {blog_topic}. Brand mood: {style}. Visual style: {image_style}.
Show an authentic scene directly related to this business category.
For hospitals or clinics, show a clean medical consultation or examination scene,
with professional medical staff and no massage, spa, or wellness treatment.
For other businesses, show their real workplace and core service.
No text, no logo, no watermark.
"""
                    (
                        blog_image_path,
                        blog_image_url
                    ) = _make_image_safe(
                        blog_retry_prompt,
                        "블로그 재시도"
                    )

                if blog_image_path:
                    blog_image_path = _add_company_name_to_image(
                        blog_image_path,
                        company,
                        business
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
                    brand_profile_id=selected_profile_id,
                    user_id=session["user_id"]
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
                    brand_profile_id=selected_profile_id,
                    user_id=session["user_id"]
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

                # 패키지 3종 생성이 모두 성공한 경우에만 월 사용량 1회 차감
                record_package_usage(session["user_id"], package_cost)
                plan_status = get_plan_status(session["user_id"])
                plan = plan_status["plan"]
                session["plan"] = plan_status["plan"]
                session["plan_used"] = plan_status["used"]
                session["plan_limit"] = plan_status["limit"]
                session["plan_remaining"] = plan_status["remaining"]
                session["plan_percent"] = plan_status["percent"]

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
        with_image=with_image,
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
        selected_profile_id=selected_profile_id,
        saved_profiles=saved_profiles,
        plan=plan
    )


@package_bp.route("/package/download")
@login_required
def download_package():
    plan_status = get_plan_status(
        session["user_id"]
    )

    if plan_status["plan"] != "PRO":
        return (
            "ZIP 전체 다운로드는 PRO 전용 기능입니다. "
            "PRO로 업그레이드해 주세요.",
            403
        )

    if not PACKAGE_ZIP_PATH.exists():
        return "먼저 마케팅 패키지를 생성해 주세요.", 404

    return send_file(
        str(PACKAGE_ZIP_PATH),
        as_attachment=True,
        download_name="marketing_package.zip"
    )
