from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = str(DOWNLOAD_DIR / "advertisement.pdf")
BLOG_PDF_PATH = str(DOWNLOAD_DIR / "blog.pdf")
SNS_PDF_PATH = str(DOWNLOAD_DIR / "sns.pdf")

FONT_PATH = Path(r"C:\Windows\Fonts\malgun.ttf")
FONT_NAME = "MalgunGothic"


def _register_font():
    if not FONT_PATH.exists():
        raise FileNotFoundError("맑은 고딕 폰트를 찾을 수 없습니다.")

    # 같은 프로세스에서 여러 번 호출되어도 안전하게 처리
    try:
        pdfmetrics.getFont(FONT_NAME)
    except KeyError:
        pdfmetrics.registerFont(
            TTFont(FONT_NAME, str(FONT_PATH))
        )


def _split_text(text: str, max_length: int = 45) -> list[str]:
    if not text:
        return [""]

    return [
        text[index:index + max_length]
        for index in range(0, len(text), max_length)
    ]


def _draw_image(pdf, image_path: str, width, y, max_height: int):
    if not image_path:
        return y

    image_file = Path(image_path)

    if not image_file.exists():
        return y

    try:
        image = ImageReader(str(image_file))
        original_width, original_height = image.getSize()

        max_width = 495

        ratio = min(
            max_width / original_width,
            max_height / original_height
        )

        image_width = original_width * ratio
        image_height = original_height * ratio
        x = (width - image_width) / 2

        pdf.drawImage(
            image,
            x,
            y - image_height,
            width=image_width,
            height=image_height,
            preserveAspectRatio=True,
            mask="auto"
        )

        return y - image_height - 30

    except Exception as error:
        print("PDF 이미지 삽입 오류:", error)
        return y


def _create_document(
    output_path: str,
    title: str,
    result: str,
    image_path: str = "",
    image_max_height: int = 300
) -> str:
    _register_font()

    # ReportLab에는 반드시 str 경로만 전달
    output_path = str(output_path)

    pdf = canvas.Canvas(
        output_path,
        pagesize=A4
    )

    width, height = A4

    pdf.setFont(FONT_NAME, 18)
    pdf.drawString(
        50,
        height - 50,
        title
    )

    y = height - 90

    y = _draw_image(
        pdf,
        image_path,
        width,
        y,
        image_max_height
    )

    pdf.setFont(FONT_NAME, 11)
    line_height = 18

    for paragraph in (result or "").splitlines():
        if not paragraph.strip():
            y -= line_height
            continue

        lines = _split_text(
            paragraph,
            max_length=45
        )

        for line in lines:
            if y < 60:
                pdf.showPage()
                pdf.setFont(FONT_NAME, 11)
                y = height - 60

            pdf.drawString(
                50,
                y,
                line
            )

            y -= line_height

    pdf.save()

    return output_path


def create_pdf(result: str, image_path: str = "") -> str:
    return _create_document(
        PDF_PATH,
        "Project Freedom AI",
        result,
        image_path,
        image_max_height=300
    )


def create_blog_pdf(result: str, image_path: str = "") -> str:
    return _create_document(
        BLOG_PDF_PATH,
        "Project Freedom AI - Blog",
        result,
        image_path,
        image_max_height=280
    )


def create_sns_pdf(result: str, image_path: str = "") -> str:
    return _create_document(
        SNS_PDF_PATH,
        "Project Freedom AI - SNS",
        result,
        image_path,
        image_max_height=320
    )
