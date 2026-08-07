from ai.image import make_image


try:
    prompt = """
    고급스러운 한국 마사지숍의 SNS 광고 이미지.
    따뜻한 조명, 깨끗한 실내, 편안한 분위기,
    프리미엄 브랜드 사진 스타일.
    이미지 안에는 글자를 넣지 말 것.
    """

    filepath = make_image(prompt)

    print("✅ 이미지 생성 성공!")
    print("저장 위치:", filepath)

except Exception as error:
    print("❌ 이미지 생성 실패")
    print(error)