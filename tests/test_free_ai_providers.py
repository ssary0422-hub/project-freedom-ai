import os
import unittest
from unittest.mock import Mock, patch

from ai.providers import (
    _available_gemini_models,
    generate_image_bytes,
    generate_text,
)


class FreeAIProviderTests(unittest.TestCase):
    def setUp(self):
        _available_gemini_models.cache_clear()

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True)
    @patch("ai.providers.requests.get")
    @patch("ai.providers.requests.post")
    def test_gemini_text_response(self, post, get):
        discovery = Mock()
        discovery.ok = True
        discovery.json.return_value = {
            "models": [{
                "name": "models/gemini-2.5-flash-lite",
                "supportedGenerationMethods": ["generateContent"],
            }]
        }
        get.return_value = discovery

        response = Mock()
        response.ok = True
        response.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "첫 번째 광고 문구"}]}}
            ]
        }
        post.return_value = response

        self.assertEqual(generate_text("광고를 만들어줘"), "첫 번째 광고 문구")
        self.assertIn("gemini-2.5-flash-lite", post.call_args.args[0])
        self.assertNotIn("test-key", post.call_args.args[0])
        self.assertEqual(
            post.call_args.kwargs["headers"]["x-goog-api-key"], "test-key"
        )

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    @patch("ai.providers.OpenAI")
    def test_openai_image_response(self, openai_cls):
        import base64

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

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_keys_are_reported(self):
        with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
            generate_text("광고")
        with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY"):
            generate_image_bytes("이미지")


if __name__ == "__main__":
    unittest.main()
