import unittest
from pathlib import Path
from flask import Flask, render_template
from routes.portfolio import portfolio_bp, WORKS


class LandingShowcaseTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.app = Flask(__name__, template_folder=str(root / 'templates'), static_folder=str(root / 'static'))
        self.app.register_blueprint(portfolio_bp)
        with self.app.test_request_context('/'):
            self.template = render_template('landing.html', works=WORKS)

    def test_selected_real_work_is_visible(self):
        for name in (
            "7days-massage-pattaya-sns.png",
            "project-freedom-conversion-ad-v1.png",
            "project-freedom-poster-v4.png",
        ):
            self.assertIn(f"showcase/{name}", self.template)
        self.assertIn("실제 게시", self.template)
        self.assertIn("자체 프로젝트", self.template)

    def test_studio_positioning_and_inquiry_path_are_present(self):
        self.assertIn("순금이의 AI 작업실", self.template)
        self.assertIn("AI가 초안을 만들고", self.template)
        self.assertIn("/services#pilot-form", self.template)
        self.assertIn("작업물 보기", self.template)

    def test_cards_open_local_work_details(self):
        from html.parser import HTMLParser
        class CardLinks(HTMLParser):
            links = []
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'a' and 'project-visual' in attrs.get('class', ''):
                    self.links.append(attrs['href'])
        parser = CardLinks()
        parser.links = []
        parser.feed(self.template)
        self.assertEqual(len(parser.links), len(WORKS))
        with self.app.test_client() as client:
            for work, href in zip(WORKS, parser.links):
                self.assertEqual(href, '/works/' + work['slug'])
                response = client.get(href)
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn(work['image'], html)
                self.assertIn('작업물 목록', html)
                self.assertNotIn('instagram.com', html)
            self.assertEqual(client.get('/works/nonexistent').status_code, 404)

    def test_walk_game_is_not_promoted(self):
        self.assertNotIn("sungeum-walk", self.template)
        self.assertNotIn("산책시키기", self.template)

    def test_landing_assets_and_accessibility_hooks_are_present(self):
        self.assertIn("landing-studio.css", self.template)
        self.assertIn("landing-studio.js", self.template)
        self.assertIn('class="skip-link"', self.template)
        self.assertIn('aria-controls="studio-menu"', self.template)


if __name__ == "__main__":
    unittest.main()
