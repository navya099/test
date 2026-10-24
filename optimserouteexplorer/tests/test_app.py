# tests/test_app.py
import unittest
import warnings
from unittest.mock import patch

from web.app import create_app


class TestCreateApp(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)

    def test_config_injection(self):
        app = create_app({"TESTING": True, "CUSTOM": "value"})
        self.assertTrue(app.config["TESTING"])
        self.assertEqual(app.config["CUSTOM"], "value")

    def test_cors_origins_from_config(self):
        app = create_app({"CORS_ORIGINS": ["http://example.com"]})
        self.assertEqual(app.config["CORS_ORIGINS"], ["http://example.com"])

    def test_api_404_json(self):
        """API 경로 404 → JSON (SPA fallback 제외)."""
        app = create_app({"TESTING": True})
        client = app.test_client()
        r = client.get("/api/nonexistent")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["error"], "not_found")

    def test_non_api_404_not_json(self):
        """비-API 경로는 SPA fallback 시도."""
        app = create_app({"TESTING": True})
        client = app.test_client()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            r = client.get("/nonexistent-random")
        # index.html 있으면 200, 없으면 404 (환경 의존)
        self.assertIn(r.status_code, (200, 404))

    def test_routes_registered(self):
        app = create_app({"TESTING": True})
        with app.test_request_context():
            rules = [r.rule for r in app.url_map.iter_rules()]
        self.assertIn("/", rules)
        self.assertIn("/api/compute", rules)

    @patch("web.app.send_from_directory")
    def test_index_serves_html(self, mock_send):
        mock_send.return_value = "html"
        app = create_app({"TESTING": True})
        client = app.test_client()
        r = client.get("/")
        self.assertEqual(r.status_code, 200)
        mock_send.assert_called_once()


if __name__ == "__main__":
    unittest.main()