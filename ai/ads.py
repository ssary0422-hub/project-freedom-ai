import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def make_ads(business, company, style):

    prompt = f"""
업종 : {business}
회사명 : {company}
분위기 : {style}

SNS 광고 문구를 5개 만들어줘.
"""

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt
    )

    return response.output_text