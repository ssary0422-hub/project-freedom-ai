import io
import unittest
from app import app


class RunningFormTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["user_id"] = 999999
            session["user_name"] = "Tester"
            session["language"] = "ko"

    def test_page_contains_upload_and_sungeum_flow(self):
        response = self.client.get("/running-form")
        self.assertEqual(response.status_code, 200)
        self.assertIn("순금이가 당신의 러닝폼".encode(), response.data)
        self.assertIn(b'id="videoInput"', response.data)
        self.assertIn(b'id="poseCanvas"', response.data)
        self.assertIn("순금 AI 총괄실장".encode(), response.data)

    def test_pose_analyzer_uses_real_mediapipe_video_landmarks(self):
        response = self.client.get("/static/running-pose-analyzer.js")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"PoseLandmarker", response.data)
        self.assertIn(b"detectForVideo", response.data)
        response.close()

    def test_preflight_accepts_supported_side_video(self):
        response = self.client.post("/running-form/preflight", data={"video": (io.BytesIO(b"test-video"), "run.mp4"), "pace": "marathon", "view": "side"}, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])

    def test_preflight_rejects_unsupported_file(self):
        response = self.client.post("/running-form/preflight", data={"video": (io.BytesIO(b"not-video"), "run.txt"), "view": "side"}, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["ok"])


if __name__ == "__main__":
    unittest.main()
