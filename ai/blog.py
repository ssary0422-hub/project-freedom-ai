import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def make_blog(topic, tone, length):

    prompt = f"""
주제 : {topic}

톤 : {tone}

길이 : {length}

SEO에 최적화된 블로그 글을 작성해줘.

제목도 포함해주고

마지막에는 해시태그도 만들어줘.
"""