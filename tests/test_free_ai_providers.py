import base64
import os
import unittest
from unittest.mock import Mock, patch

from ai.providers import generate_image_bytes, generate_text, provider_status


class AIProviderTests(unittest.TestCase):
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    @patch("ai.providers.OpenAI")
    def test_openai_text_response(self, openai_cls):
        openai_cls.return_value.responses.create.return_value = Mock(
            output_text="첫 번째 광고 문구"
        )

        self.assertEqual(generate_text("광고를 만들어줘"), "첫 번째 광고 문구")
        openai_cls.return_value.responses.create.assert_called_once_with(
            model="gpt-5.4",
            input="광고를 만들어줘",
            max_output_tokens=8192,
        )

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    @patch("ai.providers.OpenAI")
    def test_openai_image_response(self, openai_cls):
        expected = b"\x89PNG\r\n\x1a\nfake-png"
        image = Mock(b64_json=base64.b64encode(expected).decode("ascii"))
        openai_cls.return_value.images.generate.return_value = Mock(data=[image])

        self.assertEqual(generate_image_bytes("러닝 광고 이미지"), expected)
        openai_cls.return_value.images.generate.assert_called_once_with(
            model="gpt-image-2",
            prompt="러닝 광고 이미지",
            size="1024x1024",
            quality="medium",
        )

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    def test_provider_status_reports_openai_for_both_modalities(self):
        status = provider_status()
        self.assertEqual(status["text_provider"], "openai")
        self.assertEqual(status["image_provider"], "openai")
        self.assertTrue(status["text_ready"])
        self.assertTrue(status["image_ready"])

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_key_is_reported(self):
        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
            generate_text("광고")
        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
            generate_image_bytes("이미지")


if __name__ == "__main__":
    unittest.main()
