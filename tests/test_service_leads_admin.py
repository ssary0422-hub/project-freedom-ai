import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from flask import Flask
from routes.services import services_bp
from routes.auth import auth_bp


class ServiceLeadsAdminTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / 'templates'))
        self.app.secret_key = 'test-only'
        self.app.context_processor(lambda: {'translation_pairs': [], 'menu_i18n': {}, 'running_i18n': {}, 't': lambda key: key, 'current_language': 'ko', 'supported_languages': {'ko': {'flag': '', 'label': '한국어'}}})
        self.app.register_blueprint(services_bp)
        self.app.register_blueprint(auth_bp)
        self.client = self.app.test_client()

    def test_admin_can_render_empty_and_populated_inbox(self):
        with self.client.session_transaction() as session:
            session['user_id'] = 1
        connection = MagicMock()
        with patch('routes.services.is_user_admin', return_value=True), patch('routes.services.init_db'), patch('routes.services._connect', return_value=connection):
            for rows in [[], [(1, '담당자', '사업장', '연락처', 'SNS', '<script>bad()</script>', 'new', '2026-09-09')]]:
                connection.cursor.return_value.fetchall.return_value = rows
                response = self.client.get('/admin/service-leads')
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                if rows:
                    self.assertIn('사업장', html)
                    self.assertIn('&lt;script&gt;bad()', html)
                    self.assertNotIn('<script>bad()', html)
                else:
                    self.assertIn('아직 신청이 없습니다', html)

    def test_non_admin_cannot_read_inbox(self):
        self.assertEqual(self.client.get('/admin/service-leads').status_code, 302)
        with self.client.session_transaction() as session:
            session['user_id'] = 2
        with patch('routes.services.is_user_admin', return_value=False), patch('routes.services._connect') as connect:
            self.assertEqual(self.client.get('/admin/service-leads').status_code, 403)
            connect.assert_not_called()
