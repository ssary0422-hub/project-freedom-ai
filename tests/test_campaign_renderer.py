import tempfile
import unittest
from pathlib import Path

from PIL import Image

from services.campaign_art_direction import ArtDirection
from services.campaign_renderer import create_safe_typographic_background, render_blog_cover, render_campaign_concept


class CampaignRendererTests(unittest.TestCase):
    def test_safe_typographic_background_has_requested_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            direction = ArtDirection(
                concept_name="safe", campaign_angle="clear", layout_family="bold_offer",
                message_angle="customer_outcome", photo_strategy="none", subject_position="right",
                headline_position="left", mood="bold", headline="Headline",
                supporting_copy="Proof", cta="Start",
                palette=("#071827", "#59e1cb", "#ffffff"), avoid=(),
            )
            output = create_safe_typographic_background(
                direction=direction, output_path=Path(tmp) / "safe.png", size=(1200, 630)
            )
            with Image.open(output) as image:
                self.assertEqual(image.size, (1200, 630))

    def test_core_layouts_render_to_instagram_portrait(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            background = root / "background.png"
            Image.new("RGB", (1024, 1024), "#35627a").save(background)
            signatures = set()
            for layout in (
                "full_bleed_photo", "split_scene", "bold_offer",
                "editorial_type", "photo_collage", "problem_solution",
            ):
                direction = ArtDirection(
                    concept_name="테스트 방향", campaign_angle="고객 문제 해결",
                    layout_family=layout, message_angle="customer_outcome",
                    photo_strategy=f"photo-{layout}", subject_position="right",
                    headline_position="left", mood="clear",
                    headline="사업 홍보물을 다르게 만드세요",
                    supporting_copy="같은 템플릿 대신 목적에 맞는 장면을 설계합니다.",
                    cta="무료로 시작하기",
                    palette=("#071827", "#59e1cb", "#f7fbff"), avoid=(),
                )
                output = render_campaign_concept(
                    background_path=background, direction=direction,
                    company="Project Freedom AI", output_path=root / f"{layout}.png",
                )
                with Image.open(output) as image:
                    self.assertEqual(image.size, (1080, 1350))
                    signatures.add(image.resize((24, 30)).tobytes())
            self.assertEqual(len(signatures), 6)

    def test_blog_cover_has_landscape_publish_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            background = root / "background.png"
            Image.new("RGB", (1024, 1024), "#35627a").save(background)
            direction = ArtDirection(
                concept_name="검색 주제", campaign_angle="유용한 답변", layout_family="editorial_type",
                message_angle="customer_problem", photo_strategy="topic_scene", subject_position="right",
                headline_position="left", mood="clear", headline="광고 콘텐츠를 다르게 만드는 방법",
                supporting_copy="검색하는 사람이 바로 이해할 수 있는 핵심 내용을 담습니다.", cta="읽어보기",
                palette=("#071827", "#59e1cb", "#f7fbff"), avoid=(),
            )
            output = render_blog_cover(
                background_path=background, direction=direction, company="Project Freedom AI",
                output_path=root / "blog.png",
            )
            with Image.open(output) as image:
                self.assertEqual(image.size, (1200, 630))

    def test_uploaded_logo_is_preserved_on_campaign_and_blog_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            background = root / "background.png"
            logo = root / "logo.png"
            Image.new("RGB", (1200, 900), "#25445b").save(background)
            Image.new("RGBA", (240, 100), (255, 0, 180, 255)).save(logo)
            direction = ArtDirection(
                concept_name="brand", campaign_angle="clear", layout_family="full_bleed_photo",
                message_angle="customer_outcome", photo_strategy="scene", subject_position="right",
                headline_position="left", mood="clear", headline="Brand headline",
                supporting_copy="Brand proof", cta="Book now",
                palette=("#071827", "#59e1cb", "#ffffff"), avoid=(),
            )
            campaign = render_campaign_concept(
                background_path=background, direction=direction, company="Seven Days",
                output_path=root / "campaign.png", logo_path=logo,
            )
            blog = render_blog_cover(
                background_path=background, direction=direction, company="Seven Days",
                output_path=root / "blog-logo.png", logo_path=logo,
            )
            for output in (campaign, blog):
                with Image.open(output).convert("RGB") as image:
                    pixels = image.getdata()
                    self.assertTrue(any(r > 240 and b > 150 and g < 30 for r, g, b in pixels))


if __name__ == "__main__":
    unittest.main()
