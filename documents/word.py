import os

from docx import Document
from docx.shared import Inches


WORD_PATH = "downloads/advertisement.docx"
BLOG_WORD_PATH = "downloads/blog.docx"
SNS_WORD_PATH = "downloads/sns.docx"


def create_word(result, image_path=""):
    os.makedirs("downloads", exist_ok=True)

    document = Document()

    document.add_heading(
        "Project Freedom AI - Advertisement",
        level=1
    )

    if image_path and os.path.exists(image_path):
        document.add_picture(
            image_path,
            width=Inches(5.5)
        )

    document.add_paragraph(result)

    document.save(WORD_PATH)

    return WORD_PATH


def create_blog_word(result, image_path=""):
    os.makedirs("downloads", exist_ok=True)

    document = Document()

    document.add_heading(
        "Project Freedom AI - Blog",
        level=1
    )

    if image_path and os.path.exists(image_path):
        document.add_picture(
            image_path,
            width=Inches(5.5)
        )

    document.add_paragraph(result)

    document.save(BLOG_WORD_PATH)

    return BLOG_WORD_PATH


def create_sns_word(result, image_path=""):
    os.makedirs("downloads", exist_ok=True)

    document = Document()

    document.add_heading(
        "Project Freedom AI - SNS",
        level=1
    )

    if image_path and os.path.exists(image_path):
        document.add_picture(
            image_path,
            width=Inches(5.5)
        )

    document.add_paragraph(result)

    document.save(SNS_WORD_PATH)

    return SNS_WORD_PATH