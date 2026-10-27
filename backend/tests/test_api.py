import asyncio
import io
import unittest
from unittest.mock import patch

from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient

from backend.main import app, health_check, lifespan, predict_image


class PredictionEndpointTests(unittest.TestCase):
    def test_health_reports_model_not_loaded_without_loading_it(self):
        response = asyncio.run(health_check())

        self.assertEqual(response.status, "ok")
        self.assertFalse(response.model_loaded)

    def test_startup_loads_classifier_before_serving_requests(self):
        async def run_lifespan():
            async with lifespan(app):
                pass

        with patch("backend.main._load_model") as load_model:
            asyncio.run(run_lifespan())

        load_model.assert_called_once_with()

    def test_localhost_origins_are_allowed_for_local_dev(self):
        client = TestClient(app)
        response = client.get("/api/health", headers={"origin": "http://0.0.0.0:5173"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "http://0.0.0.0:5173")

    def test_rejects_unsupported_extension(self):
        self.assert_upload_error("scan.gif", b"not an image", 400, "JPG, JPEG, or PNG")

    def test_rejects_image_content_that_does_not_match_allowed_format(self):
        self.assert_upload_error("scan.png", b"not an image", 400, "not a readable image")

    def test_rejects_empty_upload(self):
        self.assert_upload_error("scan.jpg", b"", 400, "empty")

    def test_rejects_oversized_upload(self):
        content = b"x" * (10 * 1024 * 1024 + 1)
        self.assert_upload_error("scan.jpg", content, 413, "10 MB")

    def assert_upload_error(self, filename, content, status_code, message):
        upload = UploadFile(file=io.BytesIO(content), filename=filename)
        with self.assertRaises(HTTPException) as raised:
            asyncio.run(predict_image(upload))
        self.assertEqual(raised.exception.status_code, status_code)
        self.assertIn(message, raised.exception.detail)


if __name__ == "__main__":
    unittest.main()
