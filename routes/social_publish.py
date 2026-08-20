from flask import Blueprint, jsonify, request

from routes.admin import admin_required
from services.social_publisher import (
    SocialPublishError,
    instagram_ready,
    publish_instagram,
    publish_threads,
    threads_ready,
)


social_publish_bp = Blueprint("social_publish", __name__, url_prefix="/admin/social-publish")


@social_publish_bp.get("/status")
@admin_required
def status():
    return jsonify({"instagram": instagram_ready(), "threads": threads_ready()})


@social_publish_bp.post("")
@admin_required
def publish():
    data = request.get_json(silent=True) or request.form
    caption = str(data.get("caption", "")).strip()
    image_urls = data.get("image_urls", [])
    if isinstance(image_urls, str):
        image_urls = [value.strip() for value in image_urls.splitlines() if value.strip()]
    platforms = data.get("platforms", ["instagram", "threads"])
    if isinstance(platforms, str):
        platforms = [value.strip() for value in platforms.split(",") if value.strip()]

    if not caption or not image_urls:
        return jsonify({"ok": False, "error": "caption과 image_urls가 필요합니다."}), 400
    if any(not str(url).startswith("https://") for url in image_urls):
        return jsonify({"ok": False, "error": "Meta가 읽을 수 있는 공개 HTTPS 이미지 주소만 사용할 수 있습니다."}), 400

    results = []
    errors = []
    for platform in platforms:
        try:
            if platform == "instagram":
                result = publish_instagram(image_urls, caption)
            elif platform == "threads":
                result = publish_threads(image_urls, caption)
            else:
                raise SocialPublishError(f"지원하지 않는 플랫폼: {platform}")
            results.append({"platform": result.platform, "post_id": result.post_id})
        except SocialPublishError as exc:
            errors.append({"platform": platform, "error": str(exc)})

    return jsonify({"ok": not errors, "results": results, "errors": errors}), (200 if not errors else 502)
