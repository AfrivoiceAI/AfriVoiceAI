import asyncio
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.services import ai


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self.is_error = status_code >= 400
        self.payload = payload

    def json(self):
        return self.payload


class FakeAsyncClient:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.request = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def post(self, url: str, **kwargs):
        self.request = {"url": url, **kwargs}
        return self.response


class GeminiTextGenerationTests(unittest.TestCase):
    def test_gemini_returns_text_and_sends_key_in_header(self):
        client = FakeAsyncClient(
            FakeResponse(
                200,
                {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"text": "A helpful "},
                                    {"text": "draft"},
                                ]
                            }
                        }
                    ]
                },
            )
        )

        with (
            patch.object(ai.settings, "google_generative_ai_api_key", "test-key"),
            patch.object(ai.settings, "gemini_model", "gemini-3.5-flash-lite"),
            patch.object(ai.httpx, "AsyncClient", return_value=client),
        ):
            result = asyncio.run(ai.gemini_text_generate("Write a welcome message"))

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["text"], "A helpful draft")
        self.assertEqual(result["model"], "gemini-3.5-flash-lite")
        self.assertEqual(
            client.request["url"],
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-3.5-flash-lite:generateContent",
        )
        self.assertEqual(client.request["headers"]["x-goog-api-key"], "test-key")
        self.assertEqual(
            client.request["json"]["contents"][0]["parts"][0]["text"],
            "Write a welcome message",
        )

    def test_gemini_requires_credentials_before_request(self):
        with (
            patch.object(ai.settings, "google_generative_ai_api_key", ""),
            patch.object(ai.settings, "gemini_model", "gemini-3.5-flash-lite"),
            patch.object(ai.httpx, "AsyncClient") as async_client,
        ):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(ai.gemini_text_generate("Write a welcome message"))

        self.assertEqual(error.exception.status_code, 503)
        self.assertIn("GOOGLE_GENERATIVE_AI_API_KEY", error.exception.detail)
        async_client.assert_not_called()

    def test_gemini_free_tier_limit_is_actionable(self):
        client = FakeAsyncClient(FakeResponse(429, {}))

        with (
            patch.object(ai.settings, "google_generative_ai_api_key", "test-key"),
            patch.object(ai.settings, "gemini_model", "gemini-3.5-flash-lite"),
            patch.object(ai.httpx, "AsyncClient", return_value=client),
        ):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(ai.gemini_text_generate("Write a welcome message"))

        self.assertEqual(error.exception.status_code, 429)
        self.assertIn("free-tier quota", error.exception.detail)


if __name__ == "__main__":
    unittest.main()
