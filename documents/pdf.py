import io
import re
from pathlib import Path

import emoji
import requests
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas


BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

EMOJI_CACHE_DIR = BASE_DIR / "downloads" / "_emoji_cache"
EMOJI_CACHE_DIR.mkdir(parents=True, exist_ok=True)

PDF_PATH = str(DOWNLOAD_DIR / "advertisement.pdf")
BLOG_PDF_PATH = str(DOWNLOAD_DIR / "blog.pdf")
SNS_PDF_PATH = str(DOWNLOAD_DIR / "sns.pdf")

FONT_NAME = "HYSMyeongJo-Medium"

TWEMOJI_BASE_URL = (
    "https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/"
    "assets/72x72"
)

HTTP_TIMEOUT = 8


def _register_font():
    """
    ReportLab 내장 CID 한글 폰트를 사용합니다.
    Windows/Render(Linux) 모두 같은 코드로 동작합니다.
    """
    try:
        pdfmetrics.getFont(FONT_NAME)
    except KeyError:
        pdfmetrics.registerFont(
            UnicodeCIDFont(FONT_NAME)
        )


def _emoji_codepoint(value: str) -> str:
    """
    Twemoji 파일명 형식으로 변환합니다.

    예:
    😎 -> 1f60e
    💆‍♀️ -> 1f486-200d-2640-fe0f
    """
    return "-".join(
        f"{ord(character):x}"
        for character in value
    )


def _get_emoji_image(emoji_text: str):
    """
    Twemoji PNG를 다운로드해서 로컬에 캐시한 뒤
    ReportLab ImageReader를 반환합니다.

    다운로드 실패 시 None을 반환해 PDF 전체 생성을 중단하지 않습니다.
    """
    codepoint = _emoji_codepoint(
        emoji_text
    )

    cache_path = (
        EMOJI_CACHE_DIR
        / f"{codepoint}.png"
    )

    if not cache_path.exists():
        url = (
            f"{TWEMOJI_BASE_URL}/"
            f"{codepoint}.png"
        )

        try:
            response = requests.get(
                url,
                timeout=HTTP_TIMEOUT
            )

            # 일부 Twemoji 파일은 FE0F를 제거한 이름으로 저장됩니다.
            if (
                response.status_code == 404
                and "-fe0f" in codepoint
            ):
                fallback_codepoint = (
                    codepoint.replace(
                        "-fe0f",
                        ""
                    )
                )

                fallback_url = (
                    f"{TWEMOJI_BASE_URL}/"
                    f"{fallback_codepoint}.png"
                )

                response = requests.get(
                    fallback_url,
                    timeout=HTTP_TIMEOUT
                )

            response.raise_for_status()

            cache_path.write_bytes(
                response.content
            )

        except Exception as error:
            print(
                "PDF 이모지 다운로드 오류:",
                emoji_text,
                error
            )
            return None

    try:
        return ImageReader(
            str(cache_path)
        )
    except Exception as error:
        print(
            "PDF 이모지 읽기 오류:",
            emoji_text,
            error
        )
        return None


def _tokenize_text(text: str):
    """
    일반 텍스트와 이모지를 분리합니다.

    반환 예:
    [
        ("text", "오늘도 "),
        ("emoji", "😎"),
        ("text", " 화이팅")
    ]
    """
    matches = emoji.emoji_list(
        text
    )

    if not matches:
        return [
            (
                "text",
                text
            )
        ]

    tokens = []
    current_index = 0

    for item in matches:
        start = item["match_start"]
        end = item["match_end"]

        if start > current_index:
            tokens.append(
                (
                    "text",
                    text[
                        current_index:start
                    ]
                )
            )

        tokens.append(
            (
                "emoji",
                item["emoji"]
            )
        )

        current_index = end

    if current_index < len(text):
        tokens.append(
            (
                "text",
                text[current_index:]
            )
        )

    return tokens


def _text_width(
    text: str,
    font_size: float
) -> float:
    if not text:
        return 0

    return pdfmetrics.stringWidth(
        text,
        FONT_NAME,
        font_size
    )


def _emoji_width(
    font_size: float
) -> float:
    # 이모지가 일반 글자보다 살짝 넓게 보이도록 설정
    return font_size * 1.12


def _token_width(
    token,
    font_size: float
) -> float:
    kind, value = token

    if kind == "emoji":
        return _emoji_width(
            font_size
        )

    return _text_width(
        value,
        font_size
    )


def _split_text_token_to_fit(
    text: str,
    max_width: float,
    font_size: float
):
    """
    긴 일반 텍스트 토큰을 PDF 실제 폭 기준으로 나눕니다.
    """
    if not text:
        return [
            ""
        ]

    pieces = []
    current = ""

    for character in text:
        candidate = (
            current + character
        )

        if (
            current
            and _text_width(
                candidate,
                font_size
            ) > max_width
        ):
            pieces.append(
                current
            )
            current = character

        else:
            current = candidate

    if current:
        pieces.append(
            current
        )

    return pieces


def _wrap_tokens(
    text: str,
    max_width: float,
    font_size: float
):
    """
    한글/영문/이모지를 섞은 문장을
    실제 PDF 폭 기준으로 여러 줄에 나눕니다.
    """
    source_tokens = _tokenize_text(
        text
    )

    lines = []
    current_line = []
    current_width = 0

    for kind, value in source_tokens:

        if kind == "emoji":
            token = (
                kind,
                value
            )

            width = _token_width(
                token,
                font_size
            )

            if (
                current_line
                and current_width + width
                > max_width
            ):
                lines.append(
                    current_line
                )

                current_line = []
                current_width = 0

            current_line.append(
                token
            )

            current_width += width
            continue

        # 일반 텍스트는 글자 단위로 안전하게 폭 계산
        pieces = _split_text_token_to_fit(
            value,
            max_width,
            font_size
        )

        for piece in pieces:
            token = (
                "text",
                piece
            )

            width = _token_width(
                token,
                font_size
            )

            if (
                current_line
                and current_width + width
                > max_width
            ):
                lines.append(
                    current_line
                )

                current_line = []
                current_width = 0

            current_line.append(
                token
            )

            current_width += width

    if current_line:
        lines.append(
            current_line
        )

    if not lines:
        lines.append(
            [
                (
                    "text",
                    ""
                )
            ]
        )

    return lines


def _draw_rich_line(
    pdf,
    tokens,
    x: float,
    y: float,
    font_size: float
):
    """
    한 줄 안에서 일반 텍스트와 이모지 PNG를 나란히 그립니다.
    """
    cursor_x = x

    pdf.setFont(
        FONT_NAME,
        font_size
    )

    for kind, value in tokens:

        if kind == "text":
            if value:
                pdf.drawString(
                    cursor_x,
                    y,
                    value
                )

                cursor_x += _text_width(
                    value,
                    font_size
                )

            continue

        emoji_size = font_size * 1.08

        emoji_image = _get_emoji_image(
            value
        )

        if emoji_image:
            # 글자 baseline과 자연스럽게 맞추기 위한 보정값
            emoji_y = (
                y
                - font_size * 0.16
            )

            pdf.drawImage(
                emoji_image,
                cursor_x,
                emoji_y,
                width=emoji_size,
                height=emoji_size,
                preserveAspectRatio=True,
                mask="auto"
            )

        else:
            # 이미지 다운로드 실패 시 원문 이모지를 시도해서 출력
            # (지원되지 않는 폰트에서는 빈 글리프가 될 수 있음)
            try:
                pdf.drawString(
                    cursor_x,
                    y,
                    value
                )
            except Exception:
                pass

        cursor_x += _emoji_width(
            font_size
        )


def _draw_image(
    pdf,
    image_path: str,
    page_width,
    y,
    max_height: int
):
    if not image_path:
        return y

    image_file = Path(
        image_path
    )

    if not image_file.is_absolute():
        image_file = (
            BASE_DIR
            / image_file
        )

    if not image_file.exists():
        return y

    try:
        image = ImageReader(
            str(image_file)
        )

        (
            original_width,
            original_height
        ) = image.getSize()

        max_width = 495

        ratio = min(
            max_width / original_width,
            max_height / original_height
        )

        image_width = (
            original_width
            * ratio
        )

        image_height = (
            original_height
            * ratio
        )

        x = (
            page_width
            - image_width
        ) / 2

        pdf.drawImage(
            image,
            x,
            y - image_height,
            width=image_width,
            height=image_height,
            preserveAspectRatio=True,
            mask="auto"
        )

        return (
            y
            - image_height
            - 30
        )

    except Exception as error:
        print(
            "PDF 이미지 삽입 오류:",
            error
        )
        return y


def _create_document(
    output_path: str,
    title: str,
    result: str,
    image_path: str = "",
    image_max_height: int = 300
) -> str:
    _register_font()

    output_path = str(
        output_path
    )

    pdf = canvas.Canvas(
        output_path,
        pagesize=A4
    )

    width, height = A4

    left_margin = 50
    right_margin = 50
    usable_width = (
        width
        - left_margin
        - right_margin
    )

    title_size = 18
    body_size = 11
    line_height = 18

    pdf.setFont(
        FONT_NAME,
        title_size
    )

    pdf.drawString(
        left_margin,
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

    for paragraph in (
        result or ""
    ).splitlines():

        if not paragraph.strip():
            y -= line_height
            continue

        wrapped_lines = _wrap_tokens(
            paragraph,
            usable_width,
            body_size
        )

        for tokens in wrapped_lines:

            if y < 60:
                pdf.showPage()

                pdf.setFont(
                    FONT_NAME,
                    body_size
                )

                y = height - 60

            _draw_rich_line(
                pdf,
                tokens,
                left_margin,
                y,
                body_size
            )

            y -= line_height

    pdf.save()

    return output_path


def create_pdf(
    result: str,
    image_path: str = ""
) -> str:
    return _create_document(
        PDF_PATH,
        "Project Freedom AI",
        result,
        image_path,
        image_max_height=300
    )


def create_blog_pdf(
    result: str,
    image_path: str = ""
) -> str:
    return _create_document(
        BLOG_PDF_PATH,
        "Project Freedom AI - Blog",
        result,
        image_path,
        image_max_height=280
    )


def create_sns_pdf(
    result: str,
    image_path: str = ""
) -> str:
    return _create_document(
        SNS_PDF_PATH,
        "Project Freedom AI - SNS",
        result,
        image_path,
        image_max_height=320
    )
