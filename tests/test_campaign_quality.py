import tempfile
import unittest
from pathlib import Path

from PIL import Image

from services.campaign_quality import evaluate_campaign_image


def review(score, *, blockers=(), approved=False):
    return {
        "score": score,
        "approved": approved,
        "issues": ["minor polish"] if score < 90 else [],
        "blockers": list(blockers),
        "strengths": ["clear"],
        "retry_instruction": "polish hierarchy",
    }


class CampaignQualityTests(unittest.TestCase):
    def evaluate(self, path, payload, expected_size=(1080, 1350)):
        return evaluate_campaign_image(
            image_path=path,
            business="AI 홍보 콘텐츠 제작",
            company="Project Freedom AI",
            campaign_request="검증된 사실만 사용",
            expected_size=expected_size,
            analyzer=lambda *_: payload,
        )

    def test_high_strict_score_is_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "campaign.png"
            Image.new("RGB", (1080, 1350), "#123456").save(path)
            result = self.evaluate(path, review(92, approved=True))
            self.assertTrue(result["approved"])
            self.assertGreaterEqual(result["score"], 90)

    def test_strict_eighty_four_calibrates_to_release_ninety(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "campaign.png"
            Image.new("RGB", (1080, 1350), "#123456").save(path)
            result = self.evaluate(path, review(84))
            self.assertEqual(result["raw_score"], 84)
            self.assertEqual(result["score"], 90)
            self.assertTrue(result["approved"])

    def test_objective_blocker_prevents_calibrated_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "campaign.png"
            Image.new("RGB", (1080, 1350), "#123456").save(path)
            result = self.evaluate(path, review(89, blockers=("clipped text",), approved=True))
            self.assertFalse(result["approved"])

    def test_wrong_dimensions_cap_the_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "campaign.png"
            Image.new("RGB", (800, 800), "#123456").save(path)
            result = self.evaluate(path, review(99, approved=True))
            self.assertEqual(result["score"], 70)
            self.assertFalse(result["approved"])


if __name__ == "__main__":
    unittest.main()
