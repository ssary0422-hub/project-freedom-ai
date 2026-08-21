import unittest

from app import app


class RequestSecurityTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_official_www_origin_can_post_to_canonical_login(self):
        response = self.client.post(
            "/login",
            base_url="https://projectfreedom-ai.com",
            headers={"Origin": "https://www.projectfreedom-ai.com"},
            data={"email": "invalid@example.com", "password": "invalid"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("이메일 또는 비밀번호가 올바르지 않습니다.".encode(), response.data)

    def test_unknown_cross_site_origin_is_still_blocked(self):
        response = self.client.post(
            "/login",
            base_url="https://projectfreedom-ai.com",
            headers={"Origin": "https://malicious.example"},
            data={"email": "invalid@example.com", "password": "invalid"},
        )
        self.assertEqual(response.status_code, 403)

    def test_authenticated_login_redirects_to_ads_home(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1

        response = self.client.get("/login")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/ads-generator")


if __name__ == "__main__":
    unittest.main()
