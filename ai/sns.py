import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def make_sns(business, company, style, platform):
    prompt = f"""
당신은 SNS 마케팅 전문가입니다.

업종: {business}
회사명: {company}
원하는 분위기: {style}
플랫폼: {platform}

다음 조건에 맞는 SNS 게시글을 작성해주세요.

1. 첫 문장은 시선을 끌게 작성
2. 이모지 포함
3. 읽기 쉽게 줄바꿈
4. 자연스러운 홍보 문구
5. 행동을 유도하는 문장 포함
6. 마지막에 해시태그 15개
7. 한국어로 작성
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt
    )

    return response.output_text