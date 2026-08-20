import io
import unittest
from unittest.mock import patch
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
        self.assertIn(b"lastVideoTimestamp", response.data)
        self.assertIn(b"timestampBase + index", response.data)
        self.assertIn(b"strikeType", response.data)
        self.assertIn(b"runnerType", response.data)
        self.assertIn(b"bestQuality", response.data)
        self.assertIn(b"contactBonus", response.data)
        self.assertIn(b"footFocus", response.data)
        response.close()

    def test_browser_hides_raw_mediapipe_errors(self):
        response = self.client.get("/static/running-form.js")
        self.assertIn(b"friendlyError", response.data)
        self.assertIn("AI 자세 추적을 다시 준비하고 있어요".encode(), response.data)
        self.assertIn(b"makeShareCard", response.data)
        self.assertIn("SNS 결과 이미지 저장".encode(), response.data)
        self.assertIn("AI 착지 프레임".encode(), response.data)
        self.assertIn("착지 확대".encode(), response.data)
        self.assertIn(b"drawContain", response.data)
        self.assertIn(b"drawApprovalStamp", response.data)
        self.assertIn("순금 검수 완료".encode(), response.data)
        self.assertIn(b"strikeConfidence", response.data)
        self.assertIn(b"nextScoreTip", response.data)
        self.assertIn("권장 범위 105~125°".encode(), response.data)
        self.assertIn("그러면 자세가 더 편안하고 안정적으로".encode(), self.client.get("/static/running-pose-analyzer.js").data)
        self.assertIn("촬영 각도·속도·조명에 따라".encode(), response.data)
        self.assertIn(b"saveRunningHistory", response.data)

    @patch("routes.running_form.save_history", return_value=81)
    @patch("routes.running_form._save_result_image", return_value="/static/generated/running/999999/result.png")
    def test_completed_running_analysis_is_saved_to_history(self, save_image, save_history):
        response = self.client.post("/running-form/history", json={"score":78,"runnerType":"포어풋형 · 전방 추진형","strikeType":"포어풋형","averageKneeAngle":104,"averageTrunkLean":17,"strikeConfidence":95,"side":"왼쪽 측면","coachMessage":"발목부터 몸 전체를 기울여서 달려봐.","image":"data:image/png;base64,test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["history_id"], 81)
        save_history.assert_called_once()
        self.assertEqual(save_history.call_args.kwargs["content_type"], "running_form")

    def test_landing_has_dedicated_running_ai_entry(self):
        response = self.client.get("/")
        self.assertIn("AI 러닝 코치 순금".encode(), response.data)
        self.assertIn("내 러닝폼 분석하기".encode(), response.data)
        self.assertIn(b'data-kind="running"', response.data)

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
