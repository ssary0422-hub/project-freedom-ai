import base64
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

    @patch.dict(
        os.environ,
        {
            "CLOUDFLARE_ACCOUNT_ID": "account-id",
            "CLOUDFLARE_API_TOKEN": "token",
        },
        clear=True,
    )
    @patch("ai.providers.requests.post")
    def test_cloudflare_image_response(self, post):
        expected = b"\xff\xd8\xfffake-jpeg"
        response = Mock()
        response.ok = True
        response.headers = {"content-type": "application/json"}
        response.json.return_value = {
            "success": True,
            "result": {"image": base64.b64encode(expected).decode("ascii")},
        }
        post.return_value = response

        self.assertEqual(generate_image_bytes("러닝 광고 이미지"), expected)

    @patch.dict(
        os.environ,
        {"CLOUDFLARE_ACCOUNT_ID": "account-id", "CLOUDFLARE_API_TOKEN": "token"},
        clear=True,
    )
    @patch("ai.providers.time.sleep")
    @patch("ai.providers.requests.post")
    def test_cloudflare_capacity_is_retried(self, post, sleep):
        busy = Mock(ok=False, status_code=429, text="Capacity temporarily exceeded")
        ready = Mock(ok=True, headers={"content-type": "image/jpeg"}, content=b"\xff\xd8\xffok")
        post.side_effect = [busy, ready]
        self.assertEqual(generate_image_bytes("SNS image"), b"\xff\xd8\xffok")
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_keys_do_not_fall_back_to_paid_ai(self):
        with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
            generate_text("광고")
        with self.assertRaisesRegex(RuntimeError, "CLOUDFLARE"):
            generate_image_bytes("이미지")


if __name__ == "__main__":
    unittest.main()
