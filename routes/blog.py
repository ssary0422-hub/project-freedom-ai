from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont
from flask import Blueprint, render_template, request, session, send_file

from ai.blog import make_blog
from ai.image import make_image
from ai.image_prompts import build_marketing_image_prompt
from ai.providers import analyze_image_json, generate_text
from database.db import save_history, get_history_item
from database.profiles import get_profiles, get_profile
from database.users import (
    get_ai_enabled,
    get_plan_status,
    record_ai_credit_usage,
)
from documents.pdf import create_blog_pdf, BLOG_PDF_PATH
from documents.word import create_blog_word, BLOG_WORD_PATH
from routes.auth import login_required
from routes.brand_library import resolve_brand_logo, resolve_brand_photo, save_files
from services.campaign_art_direction import create_art_directions
from services.campaign_renderer import create_safe_typographic_background, render_blog_cover
from services.campaign_quality import evaluate_campaign_image
from services.campaign_budget import generate_with_bounded_backgrounds

blog_bp = Blueprint("blog", __name__)
BASE_DIR = Path(__file__).resolve().parent.parent


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
@login_required
def blog():
    return _blog_page()


@blog_bp.route("/blog", methods=["POST"])
@login_required
def generate_blog():
    return _blog_page()


@blog_bp.post("/blog/finalize")
@login_required
def finalize_blog():
    history_id = request.form.get("history_id", type=int)
    item = get_history_item(history_id, session["user_id"]) if history_id else None
    if not item or item[6] != "blog":
        return _blog_page()

    uploaded_media = save_files(
        session["user_id"], request.files.getlist("blog_photos"), "photo"
    )
    return render_template(
        "blog.html",
        result=item[4] or "",
        image_url=item[5] or "",
        business=item[1] or "",
        company=item[2] or "",
        topic="",
        tone=item[3] or "",
        length="",
        image_style="AI 추천",
        custom_image_style="",
        with_image=False,
        error="" if uploaded_media else "사진이 선택되지 않았습니다.",
        saved_profiles=get_profiles(session["user_id"]),
        selected_profile_id=None,
        loaded_profile_name="",
        uploaded_media=uploaded_media,
        history_id=history_id,
        final_preview=bool(uploaded_media),
    )


def _blog_page():
    result = ""
    error = ""
    image_url = ""
    business = ""
    company = ""
    topic = ""
    tone = ""
    length = ""
    image_style = "AI 추천"
    custom_image_style = ""
    with_image = False
    uploaded_media = []
    history_id = None
    final_preview = False

    user_id = session["user_id"]
    saved_profiles = get_profiles(user_id)
    selected_profile_id = request.args.get("profile_id", type=int)
    loaded_profile_name = ""

    if request.method == "GET" and selected_profile_id:
        selected_profile = get_profile(
            selected_profile_id,
            user_id,
        )
        if selected_profile:
            business = selected_profile[1] or ""
            company = selected_profile[2] or ""
            tone = selected_profile[3] or ""
            loaded_profile_name = company or business

    if request.method == "POST":
        if not get_ai_enabled():
            error = "현재 AI 생성 시스템이 점검 중입니다. 잠시 후 다시 이용해주세요."
            return render_template(
                "blog.html",
                result=result,
                image_url=image_url,
                business=business,
                company=company,
                topic=topic,
                tone=tone,
                length=length,
                image_style=image_style,
        custom_image_style=custom_image_style,
                with_image=with_image,
                error=error,
                saved_profiles=saved_profiles,
                selected_profile_id=selected_profile_id,
                loaded_profile_name=loaded_profile_name,
            )

        business = request.form.get("business", "").strip()
        company = request.form.get("company", "").strip()
        topic = request.form.get("topic", "").strip()
        tone = request.form.get("tone", "").strip()
        length = request.form.get("length", "").strip()
        image_style = request.form.get("image_style", "AI 추천").strip()
        custom_image_style = request.form.get("custom_image_style", "").strip()
        effective_image_style = custom_image_style or image_style
        with_image = request.form.get("with_image") == "on"

        required_credits = 3 if with_image else 1
        credit_status = get_plan_status(
            session["user_id"],
            required_credits=required_credits
        )

        if not credit_status["can_generate"]:
            error = (
                f"{credit_status['plan']} 요금제의 AI 크레딧이 부족합니다. "
                f"현재 {credit_status['remaining']}크레딧 남음 · "
                f"이번 블로그 생성은 {required_credits}크레딧이 필요합니다."
            )
            return render_template(
                "blog.html",
                result=result,
                image_url=image_url,
                business=business,
                company=company,
                topic=topic,
                tone=tone,
                length=length,
                image_style=image_style,
        custom_image_style=custom_image_style,
                with_image=with_image,
                error=error,
                saved_profiles=saved_profiles,
                selected_profile_id=selected_profile_id,
                loaded_profile_name=loaded_profile_name,
            )

        if business and company and topic and tone and length:
            result = make_blog(
                topic, tone, length,
                language=session.get("language", "ko"),
                business=business, company=company,
                uploaded_photo_names=(),
            )
            image_path = ""

            if with_image:
                logo_path = resolve_brand_logo(session["user_id"], request.files.get("real_logo"), "blog-logo")
                subject_path = resolve_brand_photo(session["user_id"], request.files.getlist("blog_photos"), "blog-photo")
                image_style_instruction = _image_style_instruction(effective_image_style)
                image_prompt = f"""
블로그 대표 이미지.

업종: {business}
회사명: {company}
주제: {topic}
분위기: {tone}
글의 길이: {length}
적용 이미지 스타일: {effective_image_style}
스타일 지시: {image_style_instruction}

블로그 주제와 실제 업종에 정확히 맞는 대표 이미지.
주제와 관계없는 마사지/스파 장면을 임의로 넣지 말 것.
깔끔하고 고급스러운 스타일.
본문 내용과 잘 어울리는 구성.
이미지 안에는 글자를 넣지 말 것.
"""
                try:
                    directions = create_art_directions(
                        business=business, company=company, request=topic,
                        media="blog", photo_count=1 if subject_path else 0, generator=generate_text, remember=True,
                    )
                    def generate_background(feedback):
                        image_prompt = build_marketing_image_prompt(
                            business=business,
                            context=f"{topic}. {feedback}. Reserve clean copy space.",
                            mood=tone,
                            image_style=effective_image_style,
                            placement="a clean landscape blog cover photograph with no text",
                            custom_concept=custom_image_style,
                        )
                        return make_image(image_prompt)

                    def render_candidate(background_path, direction, round_index, direction_index):
                        output_path = BASE_DIR / "static" / "generated" / f"finished-blog-{uuid4().hex[:10]}.png"
                        render_blog_cover(
                            background_path=background_path, direction=direction,
                            company=company, output_path=output_path, logo_path=logo_path,
                        )
                        return output_path

                    budgeted = generate_with_bounded_backgrounds(
                        directions=directions,
                        uploaded_background=subject_path,
                        generate_background=generate_background,
                        render_candidate=render_candidate,
                        create_safe_background=lambda direction: create_safe_typographic_background(
                            direction=direction,
                            output_path=BASE_DIR / "static" / "generated" / f"safe-blog-{uuid4().hex[:10]}.png",
                            size=(1200, 630),
                        ),
                        evaluate_candidate=lambda candidate: evaluate_campaign_image(
                            image_path=candidate, business=business, company=company,
                            campaign_request=topic, media="blog cover",
                            expected_size=(1200, 630), analyzer=analyze_image_json,
                        ),
                    )
                    image_path = budgeted.output_path.relative_to(BASE_DIR).as_posix()
                    image_url = "/" + Path(image_path).as_posix()
                except Exception as image_error:
                    print("블로그 이미지 생성 실패:", image_error)
                    error = (
                        "블로그 글은 생성되었지만 이미지 생성에 실패했습니다. "
                        f"오류: {image_error}"
                    )

            history_id = save_history(
                business, company, tone, result, image_url,
                content_type="blog",
                user_id=session["user_id"]
            )
            create_blog_word(result, image_path, company)
            create_blog_pdf(result, image_path)

            used_credits = 3 if with_image and image_url else 1
            record_ai_credit_usage(
                session["user_id"],
                "BLOG_IMAGE" if used_credits == 3 else "BLOG_TEXT",
                used_credits
            )

            credit_status = get_plan_status(session["user_id"])
            session["plan"] = credit_status["plan"]
            session["plan_used"] = credit_status["used"]
            session["plan_limit"] = credit_status["limit"]
            session["plan_remaining"] = credit_status["remaining"]
            session["plan_percent"] = credit_status["percent"]

    return render_template(
        "blog.html",
        result=result,
        image_url=image_url,
        business=business,
        company=company,
        topic=topic,
        tone=tone,
        length=length,
        image_style=image_style,
        uploaded_media=uploaded_media,
        custom_image_style=custom_image_style,
        with_image=with_image,
        error=error,
        saved_profiles=saved_profiles,
        selected_profile_id=selected_profile_id,
        loaded_profile_name=loaded_profile_name,
        history_id=history_id,
        final_preview=final_preview,
    )


@blog_bp.route("/blog/download/word")
@login_required
def download_blog_word():
    path = Path(BLOG_WORD_PATH)

    if not path.exists():
        return "먼저 블로그 글을 생성해 주세요.", 404

    return send_file(
        str(path),
        as_attachment=True,
        download_name="blog.docx"
    )


@blog_bp.route("/blog/download/pdf")
@login_required
def download_blog_pdf():
    path = Path(BLOG_PDF_PATH)

    if not path.exists():
        return "먼저 블로그 글을 생성해 주세요.", 404

    return send_file(
        str(path),
        as_attachment=True,
        download_name="blog.pdf"
    )
