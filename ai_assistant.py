import os
from datetime import datetime
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

print("=" * 50)
print("🤖 Project Freedom AI")
print("=" * 50)

while True:
    print("\n1. AI 사업 아이디어")
    print("2. 광고 문구 만들기")
    print("3. 블로그 글쓰기")
    print("4. 종료")

    menu = input("\n번호를 선택하세요 : ")

    if menu == "1":
        prompt = "초보자도 시작할 수 있는 AI 사업 아이디어 10개를 알려줘."

    elif menu == "2":
        business = input("업종을 입력하세요 : ")
        company = input("회사명을 입력하세요 : ")
        style = input("원하는 분위기 : ")

        prompt = f"""
업종 : {business}
회사명 : {company}
분위기 : {style}

SNS 광고 문구 5개를 만들어줘.
각 문구는 100자 이내로 작성하고 이모지도 넣어줘.
"""

    elif menu == "3":

        topic = input("블로그 주제를 입력하세요 : ")
        target = input("누구를 위한 글인가요? : ")
        tone = input("글의 분위기(친근함/전문적/재미있게) : ")

        prompt = f"""
주제 : {topic}

대상 : {target}

분위기 : {tone}

SEO를 고려한 블로그 글을 작성해주세요.

조건

- 제목 작성
- 소제목 포함
- 1000자 이상
- 마지막에 요약
- 해시태그 15개
"""
    elif menu == "4":
        print("프로그램을 종료합니다.")
        break

    else:
        print("잘못 입력했습니다.")
        continue

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt
    )

    print("\n🤖 AI 답변")
    print("-" * 50)
    print(response.output_text)
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(response.output_text)

    print(f"\n💾 {filename} 파일로 저장되었습니다.")