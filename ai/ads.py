import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def make_ads(
    business,
    company,
    style,
    count=5
):

    prompt = f"""
당신은 전문 광고 카피라이터입니다.

업종: {business}
회사명: {company}
분위기: {style}

위 브랜드에 어울리는 광고 문구를
{count}개 만들어주세요.

각 광고는 읽기 쉽고,
고객의 관심을 끌 수 있도록 작성해주세요.

한국어로 작성해주세요.
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt
    )

    return response.output_text