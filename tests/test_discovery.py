import unittest
from xml.etree.ElementTree import fromstring

from flask import Flask

from routes.discovery import discovery_bp


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(discovery_bp)
        self.client = app.test_client()

    def test_public_sitemap_is_valid_and_does_not_use_request_host(self):
        response = self.client.get("/sitemap.xml", headers={"Host": "untrusted.example"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/xml")
        root = fromstring(response.data)
        self.assertEqual(root.tag, "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
        urls = [node.text for node in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        self.assertIn("https://projectfreedom-ai.com/static/tools/subtitle-check/index.html", urls)
        self.assertEqual(len(urls), len(set(urls)))
        self.assertTrue(all(url.startswith("https://projectfreedom-ai.com/") for url in urls))
        self.assertFalse(any(part in url for url in urls for part in ("admin", "login", "books", "?", "#")))

    def test_robots_advertises_sitemap(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertIn(b"Sitemap: https://projectfreedom-ai.com/sitemap.xml\n", response.data)


if __name__ == "__main__":
    unittest.main()
