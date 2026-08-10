import base64
import os
import uuid
from datetime import datetime

from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def make_image(prompt: str) -> str:
    """프롬프트로 이미지를 생성하고 저장 경로를 반환합니다."""

    if not prompt.strip():
        raise ValueError("이미지 설명을 입력해 주세요.")

    output_folder = os.path.join(
        "static",
        "generated"
    )

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    response = client.images.generate(
        model="gpt-image-2",
        prompt=prompt
    )

    image_base64 = response.data[0].b64_json

    if not image_base64:
        raise RuntimeError(
            "이미지 데이터를 받지 못했습니다."
        )

    image_bytes = base64.b64decode(
        image_base64
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    unique_id = uuid.uuid4().hex[:8]

    filename = (
        f"image_{timestamp}_{unique_id}.png"
    )

    filepath = os.path.join(
        output_folder,
        filename
    )

    with open(filepath, "wb") as image_file:
        image_file.write(image_bytes)

    return filepath