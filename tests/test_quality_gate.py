import unittest
from unittest.mock import Mock

from ai.quality import content_quality_issues, generate_with_quality_check


class ContentQualityGateTests(unittest.TestCase):
    def test_detects_short_copy_and_missing_company(self):
        issues = content_quality_issues("짧은 문구", company="싸리런", min_chars=40)
        self.assertIn("업체명 누락", issues)
        self.assertTrue(any("너무 짧음" in issue for issue in issues))

    def test_rewrites_failed_draft_once(self):
        generate = Mock(side_effect=["너무 짧음", "싸리런의 구체적인 혜택을 설명하는 충분한 길이의 최종 광고 문구입니다."])
        result = generate_with_quality_check(generate, "광고 작성", company="싸리런", min_chars=30)
        self.assertIn("싸리런", result)
        self.assertEqual(generate.call_count, 2)

    def test_keeps_passing_result_without_extra_cost(self):
        good = "싸리런과 함께 초보자도 편안하게 시작하는 주말 러닝 수업을 지금 신청하세요."
        generate = Mock(return_value=good)
        self.assertEqual(generate_with_quality_check(generate, "광고 작성", company="싸리런", min_chars=30), good)
        self.assertEqual(generate.call_count, 1)

    def test_detects_unfinished_placeholder(self):
        issues = content_quality_issues(
            "싸리런 자세한 내용은 [직접 입력 필요]에서 확인하세요.",
            company="싸리런",
            min_chars=20,
        )
        self.assertIn("사용자에게 노출하면 안 되는 미완성 표식 포함", issues)

    def test_repair_never_returns_placeholder(self):
        generate = Mock(side_effect=[
            "싸리런은 좋은 서비스입니다. 지금 [직접 입력 필요]에서 확인해보세요.",
            "싸리런은 좋은 서비스입니다. 지금 [직접 입력 필요]에서 확인해보세요.",
        ])
        result = generate_with_quality_check(
            generate, "광고 작성", company="싸리런", min_chars=20
        )
        self.assertNotIn("직접 입력 필요", result)
        self.assertIn("업체에 문의", result)

    def test_detects_internal_image_direction(self):
        issues = content_quality_issues(
            "싸리런 이용법을 안내합니다.\n[AI 보조 이미지]\n꾸준히 실천해 보세요.",
            company="싸리런",
            min_chars=20,
        )
        self.assertIn("사용자에게 노출하면 안 되는 미완성 표식 포함", issues)


if __name__ == "__main__":
    unittest.main()
