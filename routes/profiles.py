from pathlib import Path
from io import BytesIO
import zipfile

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    send_file,
    session
)

from database.profiles import (
    get_profiles,
    get_profile,
    save_profile,
    delete_profile,
)

from database.db import (
    get_brand_history,
    get_package_history,
    delete_package_history,
    save_history_version,
    restore_history_version,
    get_history_item,
)

from ai.ads import make_ads
from ai.blog import make_blog
from ai.sns import make_sns

from routes.auth import login_required

from routes.package import (
    _make_image_safe,
    _make_sns_image,
    _is_fun_animal_style,
    _animal_prompt_name,
    _brand_tagline_for_business,
)

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


BASE_DIR = Path(__file__).resolve().parent.parent


profiles_bp = Blueprint("profiles", __name__)


@profiles_bp.route("/profiles", methods=["GET", "POST"])
@login_required
def profiles():
    error = ""

    if request.method == "POST":
        business = request.form.get("business", "").strip()
        company = request.form.get("company", "").strip()
        style = request.form.get("style", "").strip()

        image_style = request.form.get(
            "image_style",
            "고급스러운 실사"
        )

        sns_platform = request.form.get(
            "sns_platform",
            "인스타그램"
        )

        blog_length = request.form.get(
            "blog_length",
            "2000자"
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
            save_profile(
                business,
                company,
                style,
                image_style,
                sns_platform,
                blog_length,
                ads_count,
                user_id=session["user_id"]
            )

            return redirect(
                url_for("profiles.profiles")
            )

    return render_template(
        "profiles.html",
        profiles=get_profiles(session["user_id"]),
        error=error
    )


@profiles_bp.route("/profiles/<int:profile_id>/history")
@login_required
def brand_history(profile_id):
    profile = get_profile(profile_id, session["user_id"])

    if not profile:
        return "브랜드 프로필을 찾을 수 없습니다.", 404

    company = profile[2]

    history_rows = get_brand_history(
        profile_id,
        session["user_id"],
        company=company
    )

    grouped_packages = {}

    for row in history_rows:
        (
            history_id,
            business,
            row_company,
            style,
            result,
            image_url,
            content_type,
            package_id,
            brand_profile_id,
            created_at
        ) = row

        group_key = package_id or f"legacy-{history_id}"

        if group_key not in grouped_packages:
            grouped_packages[group_key] = {
                "package_id": package_id,
                "created_at": created_at,
                "items": []
            }

        grouped_packages[group_key]["items"].append({
            "id": history_id,
            "business": business,
            "company": row_company,
            "style": style,
            "result": result,
            "image_url": image_url,
            "content_type": content_type or "general",
            "created_at": created_at
        })

    packages = list(grouped_packages.values())

    return render_template(
        "brand_history.html",
        profile=profile,
        packages=packages
    )


@profiles_bp.route(
    "/profiles/<int:profile_id>/history/<package_id>"
)
@login_required
def package_detail(profile_id, package_id):
    profile = get_profile(profile_id, session["user_id"])

    if not profile:
        return "브랜드 프로필을 찾을 수 없습니다.", 404

    current_rows = get_package_history(
        package_id,
        brand_profile_id=profile_id,
        current_only=True,
        user_id=session["user_id"]
    )

    all_rows = get_package_history(
        package_id,
        brand_profile_id=profile_id,
        current_only=False,
        user_id=session["user_id"]
    )

    if not all_rows:
        return "마케팅 패키지 기록을 찾을 수 없습니다.", 404

    items = []

    for row in current_rows:
        (
            history_id,
            business,
            company,
            style,
            result,
            image_url,
            content_type,
            row_package_id,
            brand_profile_id,
            created_at,
            version,
            is_current
        ) = row

        items.append({
            "id": history_id,
            "business": business,
            "company": company,
            "style": style,
            "result": result,
            "image_url": image_url,
            "content_type": content_type or "general",
            "created_at": created_at,
            "version": version
        })

    versions_by_type = {
        "ads": [],
        "blog": [],
        "sns": []
    }

    for row in all_rows:
        content_type = (
            row[6]
            or "general"
        )

        if content_type not in versions_by_type:
            continue

        versions_by_type[
            content_type
        ].append({
            "id": row[0],
            "result": row[4],
            "image_url": row[5],
            "created_at": row[9],
            "version": row[10],
            "is_current": bool(row[11])
        })

    created_at = (
        all_rows[-1][9]
        if all_rows
        else ""
    )

    return render_template(
        "package_detail.html",
        profile=profile,
        package_id=package_id,
        created_at=created_at,
        items=items,
        versions_by_type=versions_by_type
    )


@profiles_bp.route(
    "/profiles/<int:profile_id>/history/<package_id>/delete",
    methods=["POST"]
)
@login_required
def delete_package(profile_id, package_id):
    profile = get_profile(profile_id, session["user_id"])

    if not profile:
        return "브랜드 프로필을 찾을 수 없습니다.", 404

    delete_package_history(
        package_id,
        brand_profile_id=profile_id,
        user_id=session["user_id"]
    )

    return redirect(
        url_for(
            "profiles.brand_history",
            profile_id=profile_id
        )
    )




@profiles_bp.route(
    "/history/download/<int:history_id>/<file_type>"
)
@login_required
def download_single_history(
    history_id,
    file_type
):
    """
    일반 생성 기록에서 해당 기록을 PDF/Word/이미지로 다시 받습니다.
    """
    if file_type not in {
        "pdf",
        "word",
        "image"
    }:
        return "지원하지 않는 파일 형식입니다.", 400

    item = get_history_item(
        history_id,
        session["user_id"]
    )

    if not item:
        return "생성 기록을 찾을 수 없습니다.", 404

    (
        _history_id,
        business,
        company,
        style,
        result,
        image_url,
        content_type
    ) = item

    image_path = _history_image_path(
        image_url
    )

    if file_type == "image":
        if not image_path:
            return "저장된 이미지 파일을 찾을 수 없습니다.", 404

        suffix = Path(
            image_path
        ).suffix or ".jpg"

        return send_file(
            image_path,
            as_attachment=True,
            download_name=(
                f"generated_image{suffix}"
            )
        )

    if content_type == "blog":
        if file_type == "pdf":
            output_path = create_blog_pdf(
                result,
                image_path
            )
            download_name = "blog.pdf"
        else:
            output_path = create_blog_word(
                result,
                image_path
            )
            download_name = "blog.docx"

    elif content_type == "sns":
        if file_type == "pdf":
            output_path = create_sns_pdf(
                result,
                image_path
            )
            download_name = "sns.pdf"
        else:
            output_path = create_sns_word(
                result,
                image_path
            )
            download_name = "sns.docx"

    else:
        if file_type == "pdf":
            output_path = create_pdf(
                result,
                image_path
            )
            download_name = "advertisement.pdf"
        else:
            output_path = create_word(
                result,
                image_path
            )
            download_name = "advertisement.docx"

    return send_file(
        output_path,
        as_attachment=True,
        download_name=download_name
    )


def _history_image_path(image_url):
    if not image_url:
        return ""

    relative = image_url.lstrip("/").replace("\\", "/")
    path = BASE_DIR / relative

    if path.exists():
        return str(path)

    return ""


def _find_package_item(rows, content_type):
    for row in rows:
        if row[6] == content_type:
            return row

    return None


@profiles_bp.route(
    "/profiles/<int:profile_id>/history/<package_id>/download/<content_type>/<file_type>"
)
@login_required
def download_history_file(
    profile_id,
    package_id,
    content_type,
    file_type
):
    if content_type not in {"ads", "blog", "sns"}:
        return "지원하지 않는 콘텐츠 종류입니다.", 400

    if file_type not in {"pdf", "word"}:
        return "지원하지 않는 파일 형식입니다.", 400

    profile = get_profile(profile_id, session["user_id"])

    if not profile:
        return "브랜드 프로필을 찾을 수 없습니다.", 404

    rows = get_package_history(
        package_id,
        brand_profile_id=profile_id,
        user_id=session["user_id"]
    )

    item = _find_package_item(
        rows,
        content_type
    )

    if not item:
        return "해당 콘텐츠 기록을 찾을 수 없습니다.", 404

    result = item[4]
    image_url = item[5]
    image_path = _history_image_path(
        image_url
    )

    if content_type == "ads":
        if file_type == "pdf":
            output_path = create_pdf(
                result,
                image_path
            )
            download_name = "advertisement.pdf"
        else:
            output_path = create_word(
                result,
                image_path
            )
            download_name = "advertisement.docx"

    elif content_type == "blog":
        if file_type == "pdf":
            output_path = create_blog_pdf(
                result,
                image_path
            )
            download_name = "blog.pdf"
        else:
            output_path = create_blog_word(
                result,
                image_path
            )
            download_name = "blog.docx"

    else:
        if file_type == "pdf":
            output_path = create_sns_pdf(
                result,
                image_path
            )
            download_name = "sns.pdf"
        else:
            output_path = create_sns_word(
                result,
                image_path
            )
            download_name = "sns.docx"

    return send_file(
        output_path,
        as_attachment=True,
        download_name=download_name
    )



@profiles_bp.route(
    "/profiles/<int:profile_id>/history/<package_id>/restore/<content_type>/<int:history_id>",
    methods=["POST"]
)
@login_required
def restore_history_content(
    profile_id,
    package_id,
    content_type,
    history_id
):
    if content_type not in {
        "ads",
        "blog",
        "sns"
    }:
        return "지원하지 않는 콘텐츠 종류입니다.", 400

    profile = get_profile(
        profile_id,
        session["user_id"]
    )

    if not profile:
        return "브랜드 프로필을 찾을 수 없습니다.", 404

    success = restore_history_version(
        history_id,
        package_id,
        profile_id,
        content_type,
        session["user_id"]
    )

    if not success:
        return "복원할 버전을 찾을 수 없습니다.", 404

    return redirect(
        url_for(
            "profiles.package_detail",
            profile_id=profile_id,
            package_id=package_id
        )
    )



@profiles_bp.route(
    "/profiles/<int:profile_id>/history/<package_id>/regenerate/<content_type>",
    methods=["POST"]
)
@login_required
def regenerate_history_content(
    profile_id,
    package_id,
    content_type
):
    """
    광고/블로그/SNS 중 하나만 다시 생성하고 새 버전으로 보존합니다.
    """
    if content_type not in {
        "ads",
        "blog",
        "sns"
    }:
        return "지원하지 않는 콘텐츠 종류입니다.", 400

    profile = get_profile(
        profile_id,
        session["user_id"]
    )

    if not profile:
        return "브랜드 프로필을 찾을 수 없습니다.", 404

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

    try:
        if content_type == "ads":
            result = make_ads(
                business,
                company,
                style,
                ads_count
            )

            # 선택한 이미지 스타일에 맞춰 광고 이미지를 재생성
            if _is_fun_animal_style(image_style):
                prompt = f"""
Cute humorous premium commercial advertising photo for {company}.

Business: {business}
Brand mood: {style}.

Two {_animal_prompt_name(image_style)} representing the exact business category: {business}.
One animal acts as a professional staff member and the other as a customer.
If the business is a hospital or clinic, show a medical consultation/examination scene,
not massage or spa. Use the authentic workplace and tools of the business. Photorealistic fur,
warm lighting, funny but polished social advertising aesthetic.
Family-friendly. No text, no logo, no watermark.
"""
            else:
                prompt = f"""
Professional commercial wellness advertisement photo.

Business: {business}
Brand: {company}
Brand mood: {style}
Visual style: {image_style}

A clean, elegant wellness studio with warm lighting and a polished interior.
A professional therapist is providing a fully clothed adult client
with a relaxing shoulder wellness treatment while seated comfortably.
Both people have natural, professional poses.
Family-friendly commercial photography.
No nudity, no suggestive pose, no text, no logo, no watermark.
"""

            image_path, image_url = _make_image_safe(
                prompt,
                "광고 재생성 1차"
            )

            # 1차 실패 시 사람 표현을 더 줄인 안전 프롬프트로 자동 재시도
            if not image_path:
                retry_prompt = f"""
Premium commercial image for a {business} brand named {company}.

A serene, upscale wellness interior with massage chairs,
soft towels, plants, warm ambient lighting and a calm luxury atmosphere.
A professional therapist and a fully clothed adult client may appear
in a natural, non-suggestive wellness setting.
Suitable for a family-friendly business advertisement.
No nudity, no sensual posing, no text, no logo, no watermark.
"""

                image_path, image_url = _make_image_safe(
                    retry_prompt,
                    "광고 재생성 2차"
                )

            # 두 번 모두 실패하면 빈 이미지 버전을 저장하지 않음
            if not image_path:
                return (
                    "광고 문구는 생성됐지만 광고 이미지 생성에 실패했습니다. "
                    "잠시 후 다시 시도해 주세요.",
                    502
                )

        elif content_type == "blog":
            blog_topic = (
                f"{company} {business} 소개와 "
                f"이용할 때 알아두면 좋은 점"
            )

            result = make_blog(
                blog_topic,
                style,
                blog_length
            )

            if _is_fun_animal_style(image_style):
                prompt = f"""
블로그 대표 이미지.

주제: {blog_topic}
브랜드 분위기: {style}

귀엽고 유머러스한 동물 웰니스 광고 사진.
선택 동물: {_animal_prompt_name(image_style)}
선택 동물 두 마리를 '{business}' 업종의 전문 직원과 고객 역할로 귀엽게 의인화.
병원/의원/정형외과라면 진료실, 의료진 가운, 상담·진찰·검사 장면으로 표현하고
마사지, 스파, 테라피 장면은 절대 사용하지 말 것.
고급 스파 인테리어와 따뜻한 조명, 실제 사진 같은 털과 디테일.
재미있고 사랑스럽지만 광고용으로 세련된 분위기.
글자, 로고, 워터마크는 넣지 말 것.
"""
            else:
                prompt = f"""
블로그 대표 이미지.

주제: {blog_topic}
브랜드 분위기: {style}
이미지 스타일: {image_style}

반드시 '{business}' 업종의 실제 환경과 핵심 서비스를 정확하게 표현.
병원/의원/정형외과라면 깨끗한 진료실, 전문 의료진,
X-ray/MRI 영상 또는 관절·척추 모형을 활용한 상담·진찰·검사 장면으로 표현할 것.
의료진이 환자의 어깨나 등을 직접 누르거나 주무르는 장면은 피하고,
마사지·도수치료처럼 보이는 장면, 스파, 테라피는 절대 사용하지 말 것.
다른 업종이라면 해당 업종의 공간, 직원, 고객, 제품 또는 서비스를 명확히 표현.
깔끔하고 전문적인 상업 사진 구도.
이미지 안에는 글자를 넣지 말 것.
"""

            image_path, image_url = _make_image_safe(
                prompt,
                "블로그 재생성"
            )

        else:
            result = make_sns(
                business,
                company,
                style,
                sns_platform
            )

            (
                image_path,
                image_url
            ) = _make_sns_image(
                company,
                business,
                sns_platform,
                style,
                image_style
            )

        save_history_version(
            business,
            company,
            style,
            result,
            image_url,
            content_type,
            package_id,
            profile_id,
            session["user_id"]
        )

    except Exception as error:
        print(
            f"{content_type} 개별 재생성 오류:",
            error
        )

        return (
            f"개별 재생성 중 오류가 발생했습니다: {error}",
            500
        )

    return redirect(
        url_for(
            "profiles.package_detail",
            profile_id=profile_id,
            package_id=package_id
        )
    )


def _zip_add_file(zip_file, file_path, archive_name):
    if not file_path:
        return

    path = Path(file_path)

    if path.exists():
        zip_file.write(
            str(path),
            archive_name
        )


def _zip_add_history_image(
    zip_file,
    image_url,
    base_name
):
    image_path = _history_image_path(
        image_url
    )

    if not image_path:
        return

    path = Path(image_path)
    suffix = path.suffix.lower()

    if suffix not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }:
        suffix = ".jpg"

    _zip_add_file(
        zip_file,
        image_path,
        f"images/{base_name}{suffix}"
    )


@profiles_bp.route(
    "/profiles/<int:profile_id>/history/<package_id>/download/zip"
)
@login_required
def download_history_zip(
    profile_id,
    package_id
):
    """
    저장된 히스토리의 광고/블로그/SNS를 다시 문서화하여
    PDF + Word + 이미지 전체를 ZIP 하나로 내려줍니다.
    ZIP 자체는 메모리에서 만들어 동시 사용자 간 파일 충돌을 줄입니다.
    """
    profile = get_profile(profile_id, session["user_id"])

    if not profile:
        return "브랜드 프로필을 찾을 수 없습니다.", 404

    rows = get_package_history(
        package_id,
        brand_profile_id=profile_id,
        user_id=session["user_id"]
    )

    if not rows:
        return "마케팅 패키지 기록을 찾을 수 없습니다.", 404

    ads_item = _find_package_item(
        rows,
        "ads"
    )

    blog_item = _find_package_item(
        rows,
        "blog"
    )

    sns_item = _find_package_item(
        rows,
        "sns"
    )

    zip_buffer = BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6
    ) as zip_file:

        if ads_item:
            ads_result = ads_item[4]
            ads_image_url = ads_item[5]
            ads_image_path = _history_image_path(
                ads_image_url
            )

            ads_pdf = create_pdf(
                ads_result,
                ads_image_path
            )

            ads_word = create_word(
                ads_result,
                ads_image_path
            )

            _zip_add_file(
                zip_file,
                ads_pdf,
                "advertisement.pdf"
            )

            _zip_add_file(
                zip_file,
                ads_word,
                "advertisement.docx"
            )

            _zip_add_history_image(
                zip_file,
                ads_image_url,
                "advertisement"
            )

        if blog_item:
            blog_result = blog_item[4]
            blog_image_url = blog_item[5]
            blog_image_path = _history_image_path(
                blog_image_url
            )

            blog_pdf = create_blog_pdf(
                blog_result,
                blog_image_path
            )

            blog_word = create_blog_word(
                blog_result,
                blog_image_path
            )

            _zip_add_file(
                zip_file,
                blog_pdf,
                "blog.pdf"
            )

            _zip_add_file(
                zip_file,
                blog_word,
                "blog.docx"
            )

            _zip_add_history_image(
                zip_file,
                blog_image_url,
                "blog"
            )

        if sns_item:
            sns_result = sns_item[4]
            sns_image_url = sns_item[5]
            sns_image_path = _history_image_path(
                sns_image_url
            )

            sns_pdf = create_sns_pdf(
                sns_result,
                sns_image_path
            )

            sns_word = create_sns_word(
                sns_result,
                sns_image_path
            )

            _zip_add_file(
                zip_file,
                sns_pdf,
                "sns.pdf"
            )

            _zip_add_file(
                zip_file,
                sns_word,
                "sns.docx"
            )

            _zip_add_history_image(
                zip_file,
                sns_image_url,
                "sns"
            )

    zip_buffer.seek(0)

    safe_package_id = "".join(
        character
        for character in str(package_id)
        if character.isalnum()
        or character in {"-", "_"}
    )

    if not safe_package_id:
        safe_package_id = "package"

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=(
            f"marketing_package_"
            f"{safe_package_id[:12]}.zip"
        )
    )


@profiles_bp.route(
    "/profiles/delete/<int:profile_id>",
    methods=["POST"]
)
@login_required
def delete(profile_id):
    delete_profile(profile_id)

    return redirect(
        url_for("profiles.profiles")
    )
