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


class GatewayTextGenerationTests(unittest.TestCase):
    def test_gateway_returns_model_text_and_model_id(self):
        client = FakeAsyncClient(
            FakeResponse(
                200,
                {"choices": [{"message": {"content": "A helpful draft"}}]},
            )
        )

        with (
            patch.object(ai.settings, "ai_gateway_api_key", "test-key"),
            patch.object(ai.settings, "ai_gateway_model", "provider/example-model"),
            patch.object(ai.httpx, "AsyncClient", return_value=client),
        ):
            result = asyncio.run(ai.gateway_text_generate("Write a welcome message"))

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["text"], "A helpful draft")
        self.assertEqual(result["model"], "provider/example-model")
        self.assertEqual(
            client.request["headers"]["Authorization"],
            "Bearer test-key",
        )

    def test_gateway_requires_credentials_before_request(self):
        with (
            patch.object(ai.settings, "ai_gateway_api_key", ""),
            patch.object(ai.settings, "ai_gateway_model", ""),
            patch.object(ai.httpx, "AsyncClient") as async_client,
        ):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(ai.gateway_text_generate("Write a welcome message"))

        self.assertEqual(error.exception.status_code, 503)
        self.assertIn("AI_GATEWAY_API_KEY", error.exception.detail)
        async_client.assert_not_called()

    def test_gateway_rate_limit_is_actionable(self):
        client = FakeAsyncClient(FakeResponse(429, {}))

        with (
            patch.object(ai.settings, "ai_gateway_api_key", "test-key"),
            patch.object(ai.settings, "ai_gateway_model", "provider/example-model"),
            patch.object(ai.httpx, "AsyncClient", return_value=client),
        ):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(ai.gateway_text_generate("Write a welcome message"))

        self.assertEqual(error.exception.status_code, 429)
        self.assertIn("rate limited", error.exception.detail)


if __name__ == "__main__":
    unittest.main()
