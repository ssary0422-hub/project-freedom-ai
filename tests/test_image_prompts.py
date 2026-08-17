import unittest

from ai.image_prompts import build_marketing_image_prompt, build_poster_background_prompt


class ImagePromptTests(unittest.TestCase):
    def test_cafe_peach_latte_is_forced_as_main_subject(self):
        prompt = build_marketing_image_prompt(
            business="카페", context="아이스 복숭아 라테", mood="따뜻함",
            image_style="실사", placement="SNS",
        )
        self.assertIn("iced peach latte", prompt)
        self.assertIn("STRICTLY NO text", prompt)
        self.assertIn("Do not substitute an unrelated", prompt)

    def test_poster_reserves_copy_space_and_bans_text(self):
        prompt = build_poster_background_prompt("카페 복숭아 라테")
        self.assertIn("negative space", prompt)
        self.assertIn("STRICTLY NO text", prompt)

    def test_product_named_in_mood_controls_subject(self):
        prompt = build_marketing_image_prompt(
            business="카페", context="광고", mood="복숭아 라테 신메뉴",
            image_style="실사", placement="광고",
        )
        self.assertIn("iced peach latte", prompt)


if __name__ == "__main__":
    unittest.main()
