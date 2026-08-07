import os
from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def make_sns(business, company, style, platform):
    prompt = f"""
당신은 전문 SNS 마케팅 콘텐츠 작가입니다.

업종: {business}
회사명: {company}
원하는 분위기: {style}
게시 플랫폼: {platform}

다음 조건을 만족하는 SNS 게시글을 한국어로 작성해 주세요.

1. 첫 문장은 시선을 끌게 작성
2. 회사명을 자연스럽게 포함
3. 이모지 포함
4. 읽기 쉽게 줄바꿈
5. 자연스러운 홍보 문구 포함
6. 방문이나 문의를 유도하는 문장 포함
7. 마지막에 관련 해시태그 15개 작성
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt
    )

    return response.output_text