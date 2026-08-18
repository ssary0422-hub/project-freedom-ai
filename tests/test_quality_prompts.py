import unittest
from unittest.mock import patch

from ai.ads import make_ads
from ai.blog import make_blog
from ai.sns import make_sns


class QualityPromptTests(unittest.TestCase):
    @patch("ai.ads.generate_text", return_value="오늘의커피 | 고객이 바로 이해하는 구체적인 혜택 | 지금 방문하세요\n" * 5)
    def test_ads_prompt_protects_mandatory_details(self, generate_text):
        make_ads("카페", "오늘의커피", "이번 주 20% 할인")
        prompt = generate_text.call_args.args[0]
        self.assertIn("hard constraint", prompt)
        self.assertIn("Never invent", prompt)
        self.assertIn("제목 | 핵심 혜택 | 행동 문구", prompt)

    @patch("ai.sns.generate_text", return_value="런바디와 함께 시작하는 초보 러닝 수업입니다. 부담 없이 첫 체험을 신청하고 꾸준한 변화를 시작하세요.\n\n#런바디 #초보러닝 #러닝수업 #건강한변화 #주말운동 #러닝코칭")
    def test_sns_prompt_is_mobile_ready_and_avoids_hashtag_spam(self, generate_text):
        make_sns("헬스장", "런바디", "첫 체험 할인", "인스타그램")
        prompt = generate_text.call_args.args[0]
        self.assertIn("mobile reading", prompt)
        self.assertIn("6 to 10 highly relevant hashtags", prompt)
        self.assertIn("never invent", prompt)

    @patch("ai.blog.generate_text", return_value=("튼튼정형외과에서 알려드리는 허리 통증 생활 관리법입니다. 무리하지 않는 범위에서 자세와 생활 습관을 점검하세요. " * 12))
    def test_blog_prompt_blocks_unverified_claims(self, generate_text):
        make_blog("허리 통증 관리법", "친절한 말투", "2000자", business="정형외과", company="튼튼정형외과")
        prompt = generate_text.call_args.args[0]
        self.assertIn("Never invent facts", prompt)
        self.assertIn("avoid diagnosis or guaranteed outcomes", prompt)
        self.assertIn("mobile-friendly paragraphs", prompt)


if __name__ == "__main__":
    unittest.main()
