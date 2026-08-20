import unittest
from pathlib import Path


class LandingShowcaseTests(unittest.TestCase):
    def test_project_freedom_95_point_result_is_the_lead_example(self):
        template = (Path(__file__).resolve().parents[1] / "templates" / "landing.html").read_text(encoding="utf-8")
        image_position = template.index("showcase/project-freedom-ai-promo-9-5.png")
        old_sns_position = template.index("showcase/approved-sns-9-2.png")
        self.assertLess(image_position, old_sns_position)
        self.assertIn("9.5 / 10", template)
        self.assertIn("순금 검수 95점", template)


if __name__ == "__main__":
    unittest.main()
