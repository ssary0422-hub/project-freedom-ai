from flask import Blueprint, render_template, request, redirect, url_for

from database.profiles import (
    get_profiles,
    save_profile,
    delete_profile,
)


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
