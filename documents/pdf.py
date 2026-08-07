import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


PDF_PATH = os.path.join(
    "downloads",
    "advertisement.pdf"
)


def create_pdf(result: str) -> str:
    os.makedirs("downloads", exist_ok=True)

    # Windows 기본 한글 폰트
    font_path = r"C:\Windows\Fonts\malgun.ttf"

    if not os.path.exists(font_path):
        raise FileNotFoundError(
            "맑은 고딕 폰트를 찾을 수 없습니다."
        )

    pdfmetrics.registerFont(
        TTFont("MalgunGothic", font_path)
    )

    pdf = canvas.Canvas(
        PDF_PATH,
        pagesize=A4
    )

    width, height = A4

    pdf.setFont("MalgunGothic", 18)
    pdf.drawString(
        50,
        height - 60,
        "Project Freedom AI"
    )

    pdf.setFont("MalgunGothic", 11)

    x = 50
    y = height - 100
    line_height = 18

    for paragraph in result.splitlines():

        # 빈 줄 유지
        if not paragraph.strip():
            y -= line_height
            continue

        # 긴 문장을 여러 줄로 나누기
        lines = split_text(
            paragraph,
            max_length=45
        )

        for line in lines:
            if y < 60:
                pdf.showPage()
                pdf.setFont("MalgunGothic", 11)
                y = height - 60

            pdf.drawString(x, y, line)
            y -= line_height

    pdf.save()

    return PDF_PATH


def split_text(text: str, max_length: int) -> list[str]:
    return [
        text[index:index + max_length]
        for index in range(
            0,
            len(text),
            max_length
        )
    ]