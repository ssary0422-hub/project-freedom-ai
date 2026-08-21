import unittest
from pathlib import Path


class LandingShowcaseTests(unittest.TestCase):
    def test_latest_four_approved_media_examples_are_visible(self):
        template = (Path(__file__).resolve().parents[1] / "templates" / "landing.html").read_text(encoding="utf-8")
        for name in (
            "project-freedom-editorial-sns-v3.png",
            "project-freedom-conversion-ad-v1.png",
            "project-freedom-blog-v1.png",
            "project-freedom-poster-v4.png",
        ):
            self.assertIn(f"showcase/{name}", template)
        self.assertEqual(template.count("순금 검수 90점"), 4)


if __name__ == "__main__":
    unittest.main()
