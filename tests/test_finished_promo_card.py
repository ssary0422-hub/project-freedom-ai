import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from services.finished_promo_card import (
    CARD_LABELS,
    _cover,
    _font,
    _thai_font_runs,
    card_quality_score,
    create_finished_promo_card,
    extract_card_copy,
)


class FinishedPromoCardTests(unittest.TestCase):
    def test_release_score_rejects_missing_or_invalid_material(self):
        self.assertGreaterEqual(
            card_quality_score(headline="Headline", benefit="Benefit", cta="Start now"),
            90,
        )
        self.assertLess(
            card_quality_score(headline="Headline", benefit="Benefit", cta="Start now", subject_path="missing.png"),
            90,
        )
        self.assertLess(
            card_quality_score(headline="?? ??", benefit="Benefit", cta="Start now"),
            90,
        )

    def test_uploaded_photo_is_cropped_to_the_fixed_non_overlapping_frame(self):
        portrait = Image.new("RGBA", (300, 900), "#ffffff")
        self.assertEqual(_cover(portrait, (448, 384)).size, (448, 384))

    def test_all_supported_languages_have_localized_card_labels(self):
        self.assertEqual(set(CARD_LABELS), {"ko", "en", "ja", "th", "zh", "es"})
        for labels in CARD_LABELS.values():
            self.assertTrue(labels["badge"])
            self.assertTrue(labels["fact"])
            self.assertTrue(labels["footer"])

    def test_bundled_fonts_cover_cjk_and_thai(self):
        missing_character = "\U0010ffff"
        for language, character in (("ko", "가"), ("ja", "あ"), ("zh", "中"), ("th", "ก")):
            font = _font(40, language=language)
            self.assertNotEqual(
                bytes(font.getmask(character)),
                bytes(font.getmask(missing_character)),
                language,
            )

    def test_thai_copy_uses_latin_fallback_for_brand_names(self):
        thai_font = _font(40, bold=True, language="th")
        runs = _thai_font_runs("บริการ AI · Project Freedom AI", thai_font, bold=True)
        rendered_text = "".join(text for text, _ in runs)
        font_names = {font.path for _, font in runs}
        self.assertEqual(rendered_text, "บริการ AI · Project Freedom AI")
        self.assertGreaterEqual(len(font_names), 2)

    def test_extracts_structured_ad_copy(self):
        self.assertEqual(
            extract_card_copy(
                "오늘 홍보는 했어? | 실제 정보로 바로 올릴 홍보물을 완성해요 | 지금 시작해보세요",
                "완성형 홍보물을 알리고 싶어요",
                "Project Freedom AI",
            ),
            ("오늘 홍보는 했어?", "실제 정보로 바로 올릴 홍보물을 완성해요", "지금 시작해보세요"),
        )

    def test_creates_1080_by_1350_png_without_fake_photo(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            with patch("services.finished_promo_card.OUTPUT_DIR", output_dir), patch(
                "services.finished_promo_card.BASE_DIR", output_dir
            ):
                relative = create_finished_promo_card(
                    business="AI 마케팅",
                    company="Project Freedom AI",
                    campaign_request="복잡하게 입력하지 말고 오늘 알리고 싶은 것만 말해주세요.",
                    result="오늘 홍보는 했어? | 실제 정보만으로 게시용 홍보물을 완성해요 | 순금이에게 맡겨보세요",
                    output_name="sample.png",
                )
                with Image.open(output_dir / relative) as image:
                    self.assertEqual(image.size, (1080, 1350))
                    self.assertEqual(image.format, "PNG")


if __name__ == "__main__":
    unittest.main()
