import unittest
from unittest.mock import patch

from app import app
from ai.company import assign_departments, run_company_task


class AiOfficeTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY="test")
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["user_id"] = 987654
            session["user_name"] = "대표"
            session["language"] = "ko"

    def test_department_assignment_is_explainable(self):
        departments = assign_departments("광고 마케팅과 랜딩페이지 개발")
        self.assertEqual(departments, ["planning", "development", "marketing"])

    def test_company_task_collects_and_summarizes(self):
        calls = []

        def fake_generator(prompt):
            calls.append(prompt)
            return "총괄 보고" if "총괄실장" in prompt else "부서 보고"

        result = run_company_task("SNS 광고 전략", generator=fake_generator)
        self.assertEqual(len(result["departments"]), 2)
        self.assertEqual(result["executive_summary"], "총괄 보고")
        self.assertEqual(len(calls), 3)

    @patch("routes.ai_office.list_ai_office_tasks", return_value=[])
    def test_page_renders(self, _):
        response = self.client.get("/ai-office")
        self.assertEqual(response.status_code, 200)
        self.assertIn("AI 본부".encode(), response.data)

    @patch("routes.ai_office.list_ai_office_tasks", return_value=[])
    @patch("routes.ai_office.save_ai_office_task", return_value=1)
    @patch("routes.ai_office.run_company_task")
    def test_submission_runs_office_and_saves(self, runner, *_):
        runner.return_value = {
            "departments": [],
            "executive_summary": "완료",
        }
        response = self.client.post(
            "/ai-office",
            data={"objective": "마케팅 계획을 세워줘", "context": "2주"},
        )
        self.assertEqual(response.status_code, 302)
        runner.assert_called_once_with("마케팅 계획을 세워줘", "2주")


if __name__ == "__main__":
    unittest.main()
