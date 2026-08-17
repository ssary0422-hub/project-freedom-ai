import base64
import os
import unittest
from unittest.mock import Mock, patch

from ai.providers import generate_image_bytes, generate_text


class FreeAIProviderTests(unittest.TestCase):
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True)
    @patch("ai.providers.requests.post")
    def test_gemini_text_response(self, post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "첫 번째 광고 문구"}]}}
            ]
        }
        post.return_value = response

        self.assertEqual(generate_text("광고를 만들어줘"), "첫 번째 광고 문구")
        self.assertIn("gemini-2.5-flash-lite", post.call_args.args[0])

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
        expected = b"fake-image"
        response = Mock()
        response.raise_for_status.return_value = None
        response.headers = {"content-type": "application/json"}
        response.json.return_value = {
            "success": True,
            "result": {"image": base64.b64encode(expected).decode("ascii")},
        }
        post.return_value = response

        self.assertEqual(generate_image_bytes("러닝 광고 이미지"), expected)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_keys_do_not_fall_back_to_paid_ai(self):
        with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
            generate_text("광고")
        with self.assertRaisesRegex(RuntimeError, "CLOUDFLARE"):
            generate_image_bytes("이미지")


if __name__ == "__main__":
    unittest.main()
