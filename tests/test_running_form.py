import base64
import io
import unittest
from unittest.mock import patch
from PIL import Image
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
        self.assertIn("순금이 AI 러닝코치".encode(), response.data)
        self.assertIn("달리는 영상만 올려봐".encode(), response.data)
        self.assertIn(b'id="videoInput"', response.data)
        self.assertIn(b'id="poseCanvas"', response.data)
        self.assertIn("분석·코칭·결과지 검수".encode(), response.data)

    def test_running_page_injects_selected_language_without_changing_analysis_contract(self):
        with self.client.session_transaction() as session:
            session["language"] = "en"
        response = self.client.get("/running-form")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"window.RUNNING_I18N", response.data)
        self.assertIn(b"Choose a running video", response.data)
        self.assertIn(b"/running-form/history", self.client.get("/static/running-form.js").data)

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
        self.assertIn(b"showCoachProgress", response.data)
        self.assertIn("순금이 코치가 분석하고 있어요".encode(), response.data)
        self.assertIn("다음 러닝에서 바꿀 한 가지".encode(), response.data)

    @patch("routes.running_form.save_history", return_value=81)
    @patch("routes.running_form._save_result_image", return_value="/static/generated/running/999999/result.png")
    def test_completed_running_analysis_is_saved_to_history_without_credits(self, save_image, save_history):
        response = self.client.post("/running-form/history", json={"score":78,"runnerType":"포어풋형 · 전방 추진형","strikeType":"포어풋형","averageKneeAngle":104,"averageTrunkLean":17,"strikeConfidence":95,"side":"왼쪽 측면","coachMessage":"발목부터 몸 전체를 기울여서 달려봐.","image":"data:image/png;base64,test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["history_id"], 81)
        save_history.assert_called_once()
        self.assertEqual(save_history.call_args.kwargs["content_type"], "running_form")
        self.assertEqual(response.get_json()["credits_used"], 0)
        self.assertTrue(response.get_json()["free_feature"])

    def test_landing_has_dedicated_running_ai_entry(self):
        response = self.client.get("/")
        self.assertIn("오늘 순금이에게 무엇을 맡길까요?".encode(), response.data)
        self.assertIn("사업 홍보 맡기기".encode(), response.data)
        self.assertIn("순금이 AI 러닝코치".encode(), response.data)
        self.assertIn(b"hero-task-card", response.data)
        self.assertIn(b'data-kind="running"', response.data)
        self.assertIn("AI 총괄실장 순금이".encode(), response.data)
        self.assertIn("오늘 무엇을 맡길까요?".encode(), response.data)
        self.assertIn("홍보·러닝 함께 보기".encode(), response.data)

    @patch("routes.poster.save_history", return_value=91)
    @patch("routes.poster._save_poster_result_image", return_value="/static/generated/poster/999999/result.png")
    def test_completed_poster_is_saved_to_history(self, save_image, save_history):
        with self.client.session_transaction() as session:
            session["poster_quality_approved"] = True
        response = self.client.post("/poster/history", json={"company":"테스트 상점","headline":"오늘 필요한 포스터","benefit":"한눈에 읽히는 핵심 혜택","offer":"지금 확인","contact":"온라인 예약","image":"data:image/png;base64,test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["history_id"], 91)
        self.assertEqual(save_history.call_args.kwargs["content_type"], "poster")

    def test_poster_browser_saves_completed_result(self):
        response = self.client.get("/static/poster-maker.js")
        self.assertIn(b"savePosterHistory", response.data)
        self.assertIn(b"/poster/history", response.data)

    @patch("routes.poster.analyze_image_json", return_value={
        "score": 94, "approved": True, "issues": [], "strengths": ["clear"], "retry_instruction": ""
    })
    @patch("routes.poster.record_ai_credit_usage")
    def test_poster_server_quality_gate_approves_ninety_plus(self, record_usage, _):
        with self.client.session_transaction() as session:
            session["poster_image_charge_pending"] = True
            session["poster_quality_attempts"] = 0
        buffer = io.BytesIO()
        Image.new("RGB", (1080, 1350), "#123456").save(buffer, "PNG")
        image = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
        response = self.client.post("/poster/quality", json={
            "company": "Project Freedom AI", "purpose": "홍보물을 자동으로 만듭니다", "image": image,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["approved"])
        self.assertEqual(response.get_json()["score"], 96)
        self.assertEqual(response.get_json()["raw_score"], 94)
        record_usage.assert_called_once_with(999999, "POSTER_IMAGE", 3)

    def test_preflight_accepts_supported_side_video_without_credits(self):
        response = self.client.post("/running-form/preflight", data={"video": (io.BytesIO(b"test-video"), "run.mp4"), "pace": "marathon", "view": "side"}, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])

    def test_preflight_rejects_unsupported_file(self):
        response = self.client.post("/running-form/preflight", data={"video": (io.BytesIO(b"not-video"), "run.txt"), "view": "side"}, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["ok"])

    def test_preflight_does_not_require_credits(self):
        response = self.client.post("/running-form/preflight", data={"video": (io.BytesIO(b"test-video"), "run.mp4"), "view": "side"}, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])


if __name__ == "__main__":
    unittest.main()
