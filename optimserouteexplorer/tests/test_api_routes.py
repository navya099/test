# tests/test_api_routes.py
import unittest
from unittest.mock import patch

from flask import Flask

from web.api_routes import api


class TestApiRoutes(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(api, url_prefix="/api")
        self.client = app.test_client()

    def test_missing_body(self):
        r = self.client.post("/api/compute", json=None)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.get_json()["error"], "bad_request")

    def test_missing_start_end(self):
        r = self.client.post("/api/compute", json={"start": [37.5, 127.0]})
        self.assertEqual(r.status_code, 400)
        self.assertIn("end", r.get_json()["message"])

    def test_invalid_coord(self):
        r = self.client.post("/api/compute", json={
            "start": "invalid", "end": [37.6, 127.1],
        })
        self.assertEqual(r.status_code, 400)

    def test_invalid_numeric(self):
        r = self.client.post("/api/compute", json={
            "start": [37.5, 127.0], "end": [37.6, 127.1],
            "n_candidates": "abc",
        })
        self.assertEqual(r.status_code, 400)

    def test_clamps_parameters(self):
        """상한 초과 → 클램프."""
        with patch("web.api_routes.compute") as mock_compute:
            mock_compute.return_value.top = []
            r = self.client.post("/api/compute", json={
                "start": [37.5, 127.0], "end": [37.6, 127.1],
                "n_candidates": 99999,
            })
            self.assertEqual(r.status_code, 200)
            call = mock_compute.call_args.kwargs
            self.assertLessEqual(call["n_candidates"], 200)

    def test_success(self):
        with patch("web.api_routes.compute") as mock_compute:
            mock_compute.return_value.top = [{"ID": 0, "fitness": 75.0}]
            r = self.client.post("/api/compute", json={
                "start": [37.5, 127.0], "end": [37.6, 127.1],
            })
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.get_json()["result"], [{"ID": 0, "fitness": 75.0}])

    def test_compute_exception(self):
        with patch("web.api_routes.compute", side_effect=RuntimeError("boom")):
            r = self.client.post("/api/compute", json={
                "start": [37.5, 127.0], "end": [37.6, 127.1],
            })
            self.assertEqual(r.status_code, 500)
            self.assertEqual(r.get_json()["error"], "internal_error")


if __name__ == "__main__":
    unittest.main()