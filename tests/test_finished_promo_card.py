import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from services.finished_promo_card import (
    create_finished_promo_card,
    extract_card_copy,
)


class FinishedPromoCardTests(unittest.TestCase):
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
