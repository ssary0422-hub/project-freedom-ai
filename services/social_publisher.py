import os
from dataclasses import dataclass

import requests


class SocialPublishError(RuntimeError):
    pass


@dataclass
class PublishResult:
    platform: str
    post_id: str


def _required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise SocialPublishError(f"{name} 환경변수가 설정되지 않았습니다.")
    return value


def _post(url, data):
    response = requests.post(url, data=data, timeout=60)
    try:
        payload = response.json()
    except ValueError as exc:
        raise SocialPublishError(f"Meta API가 올바르지 않은 응답을 반환했습니다: {response.text[:300]}") from exc
    if not response.ok or payload.get("error"):
        error = payload.get("error", {})
        message = error.get("message") or str(payload)
        raise SocialPublishError(message)
    return payload


def instagram_ready():
    return bool(os.environ.get("INSTAGRAM_USER_ID", "").strip() and os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip())


def threads_ready():
    return bool(os.environ.get("THREADS_ACCESS_TOKEN", "").strip())


def publish_instagram(image_urls, caption):
    user_id = _required("INSTAGRAM_USER_ID")
    token = _required("INSTAGRAM_ACCESS_TOKEN")
    version = os.environ.get("META_GRAPH_VERSION", "v24.0").strip()
    base = f"https://graph.facebook.com/{version}"

    if not image_urls:
        raise SocialPublishError("인스타그램에 올릴 이미지가 없습니다.")

    if len(image_urls) == 1:
        created = _post(f"{base}/{user_id}/media", {
            "image_url": image_urls[0], "caption": caption, "access_token": token,
        })
    else:
        children = []
        for image_url in image_urls[:10]:
            child = _post(f"{base}/{user_id}/media", {
                "image_url": image_url,
                "is_carousel_item": "true",
                "access_token": token,
            })
            children.append(child["id"])
        created = _post(f"{base}/{user_id}/media", {
            "media_type": "CAROUSEL",
            "children": ",".join(children),
            "caption": caption,
            "access_token": token,
        })

    published = _post(f"{base}/{user_id}/media_publish", {
        "creation_id": created["id"], "access_token": token,
    })
    return PublishResult("instagram", published["id"])


def publish_threads(image_urls, caption):
    token = _required("THREADS_ACCESS_TOKEN")
    base = "https://graph.threads.net/v1.0/me"
    if not image_urls:
        raise SocialPublishError("Threads에 올릴 이미지가 없습니다.")

    if len(image_urls) == 1:
        created = _post(f"{base}/threads", {
            "media_type": "IMAGE",
            "image_url": image_urls[0],
            "text": caption,
            "access_token": token,
        })
    else:
        children = []
        for image_url in image_urls[:20]:
            child = _post(f"{base}/threads", {
                "media_type": "IMAGE",
                "image_url": image_url,
                "is_carousel_item": "true",
                "access_token": token,
            })
            children.append(child["id"])
        created = _post(f"{base}/threads", {
            "media_type": "CAROUSEL",
            "children": ",".join(children),
            "text": caption,
            "access_token": token,
        })

    published = _post(f"{base}/threads_publish", {
        "creation_id": created["id"], "access_token": token,
    })
    return PublishResult("threads", published["id"])
