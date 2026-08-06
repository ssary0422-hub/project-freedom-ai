import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def make_blog(topic, tone, length):
    prompt = f"""
당신은 전문 블로그 콘텐츠 작가입니다.

주제: {topic}
글의 분위기: {tone}
글의 길이: {length}

다음 조건에 맞춰 한국어 블로그 글을 작성해주세요.

1. 클릭하고 싶은 제목
2. 자연스러운 도입부
3. 소제목이 포함된 본문
4. 읽기 편한 문단 구성
5. 마지막 요약
6. 관련 해시태그 15개
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt
    )

    return response.output_text