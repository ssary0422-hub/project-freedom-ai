"""Build the Project Freedom AI release-gate sample with UTF-8 source copy."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.finished_promo_card import (
    card_quality_score,
    create_finished_promo_card,
    extract_card_copy,
)


RESULT = (
    "광고 제작, 이제 어렵게 시작하지 마세요 | "
    "실제 사업 정보만 입력하면 게시 준비가 된 홍보 콘텐츠를 빠르게 완성합니다 | "
    "Project Freedom AI에서 지금 시작하세요"
)
REQUEST = "광고 문구와 SNS 홍보물을 한곳에서 쉽고 빠르게 만듭니다"


if __name__ == "__main__":
    headline, benefit, cta = extract_card_copy(RESULT, REQUEST, "Project Freedom AI")
    output = create_finished_promo_card(
        business="AI 홍보 콘텐츠 제작 서비스",
        company="Project Freedom AI",
        campaign_request=REQUEST,
        result=RESULT,
        output_name="project-freedom-ai-real-materials-90plus.png",
        subject_path="static/showcase/approved-sns-9-2.png",
        logo_path="static/brand/sungeum-3d-official.png",
        website_url="https://project-freedom-ai.onrender.com",
        map_url="",
        language="ko",
    )
    print(output)
    print(card_quality_score(headline=headline, benefit=benefit, cta=cta, subject_path="static/showcase/approved-sns-9-2.png"))
