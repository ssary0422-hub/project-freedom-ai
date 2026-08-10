import base64
import gc
import os
import uuid
from datetime import datetime
from pathlib import Path

from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


BASE_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = BASE_DIR / "static" / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def _is_render() -> bool:
    return bool(os.getenv("RENDER"))


def _cleanup_old_images(keep: int = 20):
    """
    Render의 임시 디스크가 불필요한 이미지로 계속 쌓이지 않도록
    오래된 생성 이미지를 정리합니다.
    """
    try:
        files = sorted(
            GENERATED_DIR.glob("image_*.*"),
            key=lambda path: path.stat().st_mtime,
            reverse=True
        )

        for old_file in files[keep:]:
            try:
                old_file.unlink()
            except OSError:
                pass

    except Exception as error:
        print("이미지 정리 오류:", error)


def make_image(prompt: str) -> str:
    """
    프롬프트로 이미지를 생성하고 저장 경로를 반환합니다.

    Render에서는 메모리 사용량을 줄이기 위해
    저품질 JPEG + 압축 출력을 사용합니다.
    """

    if not prompt.strip():
        raise ValueError("이미지 설명을 입력해 주세요.")

    # Render Free에서는 base64 데이터 자체를 작게 받아
    # 메모리 피크를 줄이는 것이 가장 중요합니다.
    if _is_render():
        quality = "low"
        compression = 55
    else:
        quality = "medium"
        compression = 75

    response = client.images.generate(
        model="gpt-image-2",
        prompt=prompt,
        size="1024x1024",
        quality=quality,
        output_format="jpeg",
        output_compression=compression
    )

    image_base64 = response.data[0].b64_json

    if not image_base64:
        raise RuntimeError("이미지 데이터를 받지 못했습니다.")

    image_bytes = base64.b64decode(image_base64)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]

    filename = f"image_{timestamp}_{unique_id}.jpg"
    filepath = GENERATED_DIR / filename

    with filepath.open("wb") as image_file:
        image_file.write(image_bytes)

    # 큰 객체를 오래 잡고 있지 않도록 즉시 해제
    del image_bytes
    del image_base64
    del response

    gc.collect()

    # Render에서는 오래된 이미지 수를 제한
    if _is_render():
        _cleanup_old_images(keep=20)

    # 기존 코드와 호환되도록 프로젝트 상대 경로 반환
    return filepath.relative_to(BASE_DIR).as_posix()
