import base64
import io
import json
import mimetypes
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageDraw, ImageFont
from flask import Blueprint, jsonify, render_template, request, session, send_file

from ai.sns import make_sns
from ai.image import make_image
from ai.image_prompts import build_marketing_image_prompt
from ai.providers import analyze_image_json, generate_text
from database.db import get_history_item, save_history, update_history_image
from database.profiles import get_profiles, get_profile
from database.users import (
    get_ai_enabled,
    get_plan_status,
    record_ai_credit_usage,
)
from documents.pdf import create_sns_pdf, SNS_PDF_PATH
from documents.word import create_sns_word, SNS_WORD_PATH
from routes.auth import login_required
from routes.brand_library import resolve_brand_logo, resolve_brand_photo
from services.finished_promo_card import create_finished_promo_card
from services.campaign_art_direction import (
    create_art_directions,
    direction_from_payload,
    serialize_directions,
)
from services.campaign_renderer import create_safe_typographic_background, render_campaign_concept
from services.campaign_quality import evaluate_campaign_image
from services.campaign_budget import generate_with_bounded_backgrounds
from services.uploaded_materials import first_valid_uploaded_image, save_uploaded_image

sns_bp = Blueprint("sns", __name__)
BASE_DIR = Path(__file__).resolve().parent.parent


def _public_image_url(path: str | Path) -> str:
    """Turn either an absolute generated path or a relative static path into a URL."""
    candidate = Path(path)
    relative = candidate.relative_to(BASE_DIR) if candidate.is_absolute() else candidate
    return "/" + relative.as_posix().lstrip("/")


def _image_data_url(path: str | Path) -> str:
    """Inline a small preview so mobile pages do not carry the full PNG payload."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate
    if not candidate.exists() or not candidate.is_file():
        return ""
    try:
        preview = Image.open(candidate).convert("RGB")
        preview.thumbnail((720, 900), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        preview.save(buffer, format="JPEG", quality=78, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception:
        mime = mimetypes.guess_type(candidate.name)[0] or "image/png"
        encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{encoded}"


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


def _generate_sns_image(business, company, style, platform, image_style, custom_image_style=""):
    effective_image_style = custom_image_style or image_style
    prompt = build_marketing_image_prompt(
        business=business,
        context=f"{platform} social post for {company}; {style}",
        mood=style,
        image_style=effective_image_style,
        placement="a square social media hero image",
        custom_concept=custom_image_style,
    )
    return make_image(prompt)


@sns_bp.post("/sns/art-directions")
@login_required
def sns_art_directions():
    """Return three cheap planning choices before generating an image."""
    if not get_ai_enabled():
        return jsonify(error="현재 AI 생성 기능을 사용할 수 없습니다."), 503
    status = get_plan_status(session["user_id"], required_credits=3)
    if not status["can_generate"]:
        return jsonify(error="이미지 생성에 필요한 AI 크레딧이 부족합니다."), 402
    data = request.get_json(silent=True) or {}
    business = str(data.get("business", "")).strip()
    company = str(data.get("company", "")).strip()
    campaign_request = str(data.get("request", "")).strip()
    if not all((business, company, campaign_request)):
        return jsonify(error="업종, 업체명, 홍보 내용을 먼저 입력해 주세요."), 400
    try:
        directions = create_art_directions(
            business=business,
            company=company,
            request=campaign_request,
            media="sns",
            photo_count=max(0, min(10, int(data.get("photo_count", 0) or 0))),
            generator=generate_text,
            remember=False,
        )
        return jsonify(directions=serialize_directions(directions))
    except Exception as exc:
        print("SNS art direction failed:", exc)
        return jsonify(error="서로 다른 디자인 방향을 만드는 데 실패했습니다. 다시 시도해 주세요."), 502


@sns_bp.route("/sns", methods=["GET"])
@login_required
def sns():
    return _sns_page()


@sns_bp.route("/sns", methods=["POST"])
@login_required
def generate_sns():
    return _sns_page()


def _sns_page():
    # Keep the credit pill and the server-side generation check on the same
    # source of truth. A long-lived login session can otherwise show stale
    # credits after usage or a plan change.
    current_status = get_plan_status(session["user_id"])
    session["plan"] = current_status["plan"]
    session["plan_used"] = current_status["used"]
    session["plan_limit"] = current_status["limit"]
    session["plan_remaining"] = current_status["remaining"]
    session["plan_percent"] = current_status["percent"]
    result = ""
    image_url = ""
    image_data_url = ""
    image_path = ""
    error = ""
    business = ""
    company = ""
    style = ""
    platform = ""
    image_style = "AI 추천"
    custom_image_style = ""
    with_image = False
    image_error = ""
    image_retry_history_id = None

    user_id = session["user_id"]
    saved_profiles = get_profiles(user_id)
    selected_profile_id = request.args.get("profile_id", type=int)
    loaded_profile_name = ""

    if request.method == "GET" and not selected_profile_id:
        assistant_brief = request.args.get("assistant_brief", "").strip()
        style = request.args.get("style", "").strip()
        if assistant_brief:
            style = f"{style}. 순금이 요청 정리: {assistant_brief}".strip(". ")

    if request.method == "GET" and selected_profile_id:
        selected_profile = get_profile(
            selected_profile_id,
            user_id,
        )
        if selected_profile:
            business = selected_profile[1] or ""
            company = selected_profile[2] or ""
            style = selected_profile[3] or ""
            loaded_profile_name = company or business

    if request.method == "POST":
        if not get_ai_enabled():
            error = "현재 AI 생성 시스템이 점검 중입니다. 잠시 후 다시 이용해주세요."
            return render_template(
                "sns.html",
                result=result,
                image_url=image_url,
                error=error,
                saved_profiles=saved_profiles,
                selected_profile_id=selected_profile_id,
                loaded_profile_name=loaded_profile_name,
                business=business,
                company=company,
                style=style,
                platform=platform,
                image_style=image_style,
        custom_image_style=custom_image_style,
                with_image=with_image
            )

        business = request.form.get("business", "").strip()
        company = request.form.get("company", "").strip()
        style = request.form.get("style", "").strip()
        platform = request.form.get("platform", "").strip()
        image_style = request.form.get("image_style", "AI 추천").strip()
        custom_image_style = request.form.get("custom_image_style", "").strip()
        effective_image_style = custom_image_style or image_style
        with_image = request.form.get("with_image") == "on"
        # Default to one finished, publishable card rather than an unlabelled
        # stock-style background. The three art directions still vary layout,
        # subject placement, message angle, and palette for each request.
        image_output_mode = request.form.get("image_output_mode", "finished_card").strip()
        selected_art_direction = request.form.get("selected_art_direction", "").strip()

        required_credits = 3 if with_image else 1
        credit_status = get_plan_status(
            session["user_id"],
            required_credits=required_credits
        )

        if not credit_status["can_generate"]:
            error = (
                f"{credit_status['plan']} 요금제의 AI 크레딧이 부족합니다. "
                f"현재 {credit_status['remaining']}크레딧 남음 · "
                f"이번 SNS 생성은 {required_credits}크레딧이 필요합니다."
            )
            return render_template(
                "sns.html",
                result=result,
                image_url=image_url,
                business=business,
                company=company,
                style=style,
                platform=platform,
                image_style=image_style,
        custom_image_style=custom_image_style,
                with_image=with_image,
                error=error,
                saved_profiles=saved_profiles,
                selected_profile_id=selected_profile_id,
                loaded_profile_name=loaded_profile_name,
            )

        if not all([business, company, style, platform]):
            error = "모든 항목을 입력해 주세요."
        else:
            try:
                result = make_sns(business, company, style, platform, language=session.get("language", "ko"))
                image_path = ""

                if with_image:
                    try:
                        if image_output_mode == "finished_card":
                            subject_path = resolve_brand_photo(session["user_id"], request.files.getlist("real_photos"), "sns-photo")
                            logo_path = resolve_brand_logo(
                                session["user_id"], request.files.get("real_logo"), "sns-logo",
                                reuse_saved=bool(request.form.get("use_saved_logo")),
                            )
                            if selected_art_direction:
                                directions = [direction_from_payload(json.loads(selected_art_direction))]
                            else:
                                directions = create_art_directions(
                                    business=business,
                                    company=company,
                                    request=style,
                                    media="sns",
                                    photo_count=1 if subject_path else 0,
                                    generator=generate_text,
                                    remember=True,
                                )

                            def generate_background(feedback):
                                return _generate_sns_image(
                                    business, company,
                                    f"{style}. {feedback}. The scene must clearly fit the exact business. "
                                    "No readable text, letters, logos, or watermark.",
                                    platform, image_style, custom_image_style,
                                )

                            def render_candidate(background_path, direction, round_index, direction_index):
                                output_path = BASE_DIR / "static" / "generated" / f"finished-sns-{uuid4().hex[:10]}.png"
                                render_campaign_concept(
                                    background_path=background_path,
                                    direction=direction,
                                    company=company,
                                    output_path=output_path,
                                    logo_path=logo_path,
                                    footer_detail=(request.form.get("website_url", "").strip() or request.form.get("map_url", "").strip()),
                                )
                                return output_path

                            budgeted = generate_with_bounded_backgrounds(
                                directions=directions,
                                uploaded_background=subject_path,
                                generate_background=generate_background,
                                render_candidate=render_candidate,
                                create_safe_background=lambda direction: create_safe_typographic_background(
                                    direction=direction,
                                    output_path=BASE_DIR / "static" / "generated" / f"safe-sns-{uuid4().hex[:10]}.png",
                                ),
                                evaluate_candidate=lambda candidate: evaluate_campaign_image(
                                    image_path=candidate,
                                    business=business,
                                    company=company,
                                    campaign_request=style,
                                    analyzer=analyze_image_json,
                                ),
                                prefer_generated_on_failure=True,
                            )
                            output_path, visual_review = budgeted.output_path, budgeted.review
                            image_path = output_path.relative_to(BASE_DIR).as_posix()
                            # The finished-card path returns a relative file path;
                            # expose it immediately so the first mobile response
                            # includes the image and history stores its URL.
                            image_url = _public_image_url(image_path)
                        else:
                            image_path = _generate_sns_image(
                                business, company, style, platform,
                                image_style, custom_image_style,
                            )
                            image_url = _public_image_url(image_path)
                    except Exception as image_exception:
                        image_error = (
                            "글은 안전하게 완성했지만 이미지 생성에 실패했어요. "
                            "같은 글을 유지한 채 이미지만 다시 만들 수 있어요."
                        )
                        print("SNS image generation failed:", image_exception)
                        # Keep the paid flow useful when the external image
                        # provider is unavailable by rendering a local,
                        # typography-led 1080x1350 card from verified copy.
                        try:
                            fallback_path = create_finished_promo_card(
                                business=business,
                                company=company,
                                campaign_request=style,
                                result=result,
                                output_name=f"finished-sns-{uuid4().hex[:10]}.png",
                                website_url=request.form.get("website_url", "").strip(),
                                map_url=request.form.get("map_url", "").strip(),
                                language=session.get("language", "ko"),
                            )
                            image_path = fallback_path
                            image_url = _public_image_url(fallback_path)
                            image_error = ""
                        except Exception as fallback_exception:
                            print("SNS safe card fallback failed:", fallback_exception)

                image_retry_history_id = save_history(
                    business, company, style, result, image_url,
                    content_type="sns",
                    user_id=session["user_id"]
                )
                create_sns_word(result, image_path, company)
                create_sns_pdf(result, image_path)

                used_credits = 3 if with_image and image_url else 1
                record_ai_credit_usage(
                    session["user_id"],
                    "SNS_IMAGE" if used_credits == 3 else "SNS_TEXT",
                    used_credits
                )

                credit_status = get_plan_status(session["user_id"])
                session["plan"] = credit_status["plan"]
                session["plan_used"] = credit_status["used"]
                session["plan_limit"] = credit_status["limit"]
                session["plan_remaining"] = credit_status["remaining"]
                session["plan_percent"] = credit_status["percent"]

            except Exception as e:
                error = f"SNS 생성 오류: {e}"
                print(error)

    if image_path:
        image_data_url = _image_data_url(image_path)

    return render_template(
        "sns.html",
        result=result,
        image_url=image_url,
        image_data_url=image_data_url,
        error=error,
        saved_profiles=saved_profiles,
        selected_profile_id=selected_profile_id,
        loaded_profile_name=loaded_profile_name,
        business=business,
        company=company,
        style=style,
        platform=platform,
        image_style=image_style,
        custom_image_style=custom_image_style,
        with_image=with_image,
        image_error=image_error,
        image_retry_history_id=image_retry_history_id,
    )


@sns_bp.post("/sns/retry-image")
@login_required
def retry_sns_image():
    history_id = request.form.get("history_id", type=int)
    item = get_history_item(history_id, session["user_id"]) if history_id else None
    if not item or item[6] != "sns":
        return "다시 만들 SNS 결과를 찾을 수 없어요.", 404

    business, company, style, result = item[1], item[2], item[3], item[4]
    platform = request.form.get("platform", "Instagram").strip()
    image_style = request.form.get("image_style", "AI 추천").strip()
    custom_image_style = request.form.get("custom_image_style", "").strip()
    credit_status = get_plan_status(session["user_id"], required_credits=2)
    image_url = ""
    image_data_url = ""
    image_path = ""
    image_error = ""
    error = ""

    if not credit_status["can_generate"]:
        error = "이미지 재생성에는 2크레딧이 필요해요."
    else:
        try:
            # Retries must use the finished-card renderer too. The old path
            # called the raw image model, yielding square art with unreliable
            # text and bypassing the 1080x1350 typography/quality pipeline.
            subject_path = resolve_brand_photo(
                session["user_id"], request.files.getlist("real_photos"), "sns-retry-photo"
            )
            logo_path = resolve_brand_logo(
                session["user_id"], request.files.get("real_logo"), "sns-retry-logo",
                reuse_saved=bool(request.form.get("use_saved_logo")),
            )
            directions = create_art_directions(
                business=business,
                company=company,
                request=style,
                media="sns",
                photo_count=1 if subject_path else 0,
                generator=generate_text,
                remember=True,
            )

            def generate_background(feedback):
                return _generate_sns_image(
                    business,
                    company,
                    f"{style}. {feedback}. The scene must clearly fit the exact business. "
                    "No readable text, letters, logos, or watermark.",
                    platform,
                    image_style,
                    custom_image_style,
                )

            def render_candidate(background_path, direction, round_index, direction_index):
                output_path = BASE_DIR / "static" / "generated" / f"finished-sns-{uuid4().hex[:10]}.png"
                render_campaign_concept(
                    background_path=background_path,
                    direction=direction,
                    company=company,
                    output_path=output_path,
                    logo_path=logo_path,
                    footer_detail="",
                )
                return output_path

            budgeted = generate_with_bounded_backgrounds(
                directions=directions,
                uploaded_background=subject_path,
                generate_background=generate_background,
                render_candidate=render_candidate,
                create_safe_background=lambda direction: create_safe_typographic_background(
                    direction=direction,
                    output_path=BASE_DIR / "static" / "generated" / f"safe-sns-{uuid4().hex[:10]}.png",
                ),
                evaluate_candidate=lambda candidate: evaluate_campaign_image(
                    image_path=candidate,
                    business=business,
                    company=company,
                    campaign_request=style,
                    analyzer=analyze_image_json,
                ),
            )
            image_path = budgeted.output_path
            image_url = _public_image_url(image_path)
            if not update_history_image(history_id, session["user_id"], image_url):
                raise RuntimeError("생성 기록에 이미지를 연결하지 못했습니다.")
            create_sns_word(result, image_path, company)
            create_sns_pdf(result, image_path)
            record_ai_credit_usage(session["user_id"], "SNS_IMAGE_RETRY", 2)
            credit_status = get_plan_status(session["user_id"])
            session["plan_remaining"] = credit_status["remaining"]
        except Exception as image_exception:
            print("SNS image retry failed:", image_exception)
            # Compatibility fallback for a temporary planning-provider outage.
            # Normal retries use the finished-card renderer above.
            try:
                image_path = _generate_sns_image(
                    business, company, style, platform,
                    image_style, custom_image_style,
                )
                image_url = _public_image_url(image_path)
                if not update_history_image(history_id, session["user_id"], image_url):
                    raise RuntimeError("retry history update failed")
                create_sns_word(result, image_path, company)
                create_sns_pdf(result, image_path)
                record_ai_credit_usage(session["user_id"], "SNS_IMAGE_RETRY", 2)
                credit_status = get_plan_status(session["user_id"])
                session["plan_remaining"] = credit_status["remaining"]
                image_error = ""
            except Exception as fallback_exception:
                print("SNS raw image retry fallback failed:", fallback_exception)
                # Last-resort local card: the user should still receive a
                # usable 1080x1350 asset when both image-provider attempts
                # are unavailable.
                try:
                    safe_path = create_finished_promo_card(
                        business=business,
                        company=company,
                        campaign_request=style,
                        result=result,
                        output_name=f"finished-sns-{uuid4().hex[:10]}.png",
                        language=session.get("language", "ko"),
                    )
                    image_url = _public_image_url(safe_path)
                    if update_history_image(history_id, session["user_id"], image_url):
                        create_sns_word(result, safe_path, company)
                        create_sns_pdf(result, safe_path)
                        record_ai_credit_usage(session["user_id"], "SNS_IMAGE_RETRY", 2)
                        image_error = ""
                    else:
                        image_url = ""
                except Exception as safe_exception:
                    print("SNS safe card retry fallback failed:", safe_exception)
                    image_url = ""
            image_error = image_error if image_url else (
                "이미지 재생성에 실패했어요. 크레딧은 차감하지 않았습니다. "
                "잠시 후 다시 눌러주세요."
            )

    if image_path:
        image_data_url = _image_data_url(image_path)

    return render_template(
        "sns.html", result=result, image_url=image_url,
        image_data_url=image_data_url,
        image_error=image_error, image_retry_history_id=history_id,
        error=error, saved_profiles=get_profiles(session["user_id"]),
        selected_profile_id=None, loaded_profile_name="", business=business,
        company=company, style=style, platform=platform, image_style=image_style,
        custom_image_style=custom_image_style, with_image=True,
    )


@sns_bp.route("/sns/download/word")
@login_required
def download_sns_word():
    path = Path(SNS_WORD_PATH)

    if not path.exists():
        return "먼저 SNS 글을 생성해 주세요.", 404

    return send_file(
        str(path),
        as_attachment=True,
        download_name="sns.docx"
    )


@sns_bp.route("/sns/download/pdf")
@login_required
def download_sns_pdf():
    path = Path(SNS_PDF_PATH)

    if not path.exists():
        return "먼저 SNS 글을 생성해 주세요.", 404

    return send_file(
        str(path),
        as_attachment=True,
        download_name="sns.pdf"
    )
