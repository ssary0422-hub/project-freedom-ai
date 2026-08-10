from flask import Blueprint, render_template, request, redirect, url_for

from database.profiles import (
    get_profiles,
    get_profile,
    save_profile,
    delete_profile,
)

from database.db import get_brand_history


profiles_bp = Blueprint(
    "profiles",
    __name__
)


@profiles_bp.route("/profiles", methods=["GET", "POST"])
def profiles():
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

        if not all([
            business,
            company,
            style
        ]):
            error = "업종, 회사명, 브랜드 분위기를 모두 입력해 주세요."

        else:
            save_profile(
                business,
                company,
                style,
                image_style,
                sns_platform,
                blog_length,
                ads_count
            )

            return redirect(
                url_for(
                    "profiles.profiles"
                )
            )

    return render_template(
        "profiles.html",
        profiles=get_profiles(),
        error=error
    )


@profiles_bp.route(
    "/profiles/<int:profile_id>/history"
)
def brand_history(profile_id):
    profile = get_profile(
        profile_id
    )

    if not profile:
        return "브랜드 프로필을 찾을 수 없습니다.", 404

    company = profile[2]

    history_rows = get_brand_history(
        profile_id,
        company=company
    )

    # package_id 기준으로 광고/블로그/SNS를 묶음
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

        # 과거 데이터는 package_id가 없으므로 개별 묶음으로 표시
        group_key = (
            package_id
            or f"legacy-{history_id}"
        )

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

    packages = list(
        grouped_packages.values()
    )

    return render_template(
        "brand_history.html",
        profile=profile,
        packages=packages
    )


@profiles_bp.route(
    "/profiles/delete/<int:profile_id>",
    methods=["POST"]
)
def delete(profile_id):
    delete_profile(
        profile_id
    )

    return redirect(
        url_for(
            "profiles.profiles"
        )
    )
