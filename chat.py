import os
import sys

from openai import OpenAI

sys.stdout.reconfigure(encoding="utf-8")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

question = input("질문을 입력하세요: ")

response = client.responses.create(
    model="gpt-5.5",
    input=question,
)

print("\n🤖 AI의 답변")
print("-" * 40)
print(response.output_text)
