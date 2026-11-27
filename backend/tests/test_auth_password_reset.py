import hashlib
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId
from fastapi import HTTPException

from app.api.routes import auth
from app.core.security import verify_password
from app.models.schemas import PasswordResetIn, PasswordResetRequestIn


class FakeUsers:
    def __init__(self, user=None):
        self.user = user

    def find_one(self, query):
        if self.user and query == {"email": self.user["email"]}:
            return self.user
        return None

    def update_one(self, query, update):
        if not self.user or (
            "_id" in query and query["_id"] != self.user["_id"]
        ):
            return SimpleNamespace(matched_count=0)

        token_hash = query.get("password_reset_token_hash")
        if token_hash:
            if self.user.get("password_reset_token_hash") != token_hash:
                return SimpleNamespace(matched_count=0)
            expiration = self.user.get("password_reset_expires_at")
            if "$gt" in query.get("password_reset_expires_at", {}):
                if not expiration or expiration <= query["password_reset_expires_at"]["$gt"]:
                    return SimpleNamespace(matched_count=0)

        self.user.update(update.get("$set", {}))
        for field in update.get("$unset", {}):
            self.user.pop(field, None)
        return SimpleNamespace(matched_count=1)


class PasswordResetTests(unittest.TestCase):
    def test_forgot_password_sends_token_without_storing_it_in_plaintext(self):
        user = {"_id": ObjectId(), "email": "creator@example.com"}
        users = FakeUsers(user)
        sent = {}

        with (
            patch.object(auth, "db", SimpleNamespace(users=users)),
            patch.object(auth.settings, "smtp_host", "smtp.example.com"),
            patch.object(auth.settings, "smtp_from_email", "hello@example.com"),
            patch.object(auth, "send_password_reset_email", side_effect=lambda email, token: sent.update(
                email=email, token=token
            )),
        ):
            result = auth.forgot_password(
                PasswordResetRequestIn(email="creator@example.com")
            )

        self.assertIn("If an account exists", result["message"])
        self.assertEqual(sent["email"], "creator@example.com")
        self.assertEqual(
            user["password_reset_token_hash"],
            hashlib.sha256(sent["token"].encode()).hexdigest(),
        )
        self.assertNotEqual(user["password_reset_token_hash"], sent["token"])
        self.assertGreater(
            user["password_reset_expires_at"],
            datetime.now(timezone.utc) + timedelta(minutes=59),
        )

    def test_reset_password_updates_password_and_consumes_token(self):
        token = "single-use-reset-token"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        user = {
            "_id": ObjectId(),
            "email": "creator@example.com",
            "password_hash": auth.hash_password("old-password"),
            "password_reset_token_hash": token_hash,
            "password_reset_expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
        }

        with patch.object(auth, "db", SimpleNamespace(users=FakeUsers(user))):
            result = auth.reset_password(
                PasswordResetIn(token=token, password="new-password")
            )

        self.assertEqual(result["message"], "Password reset successfully. You can now sign in.")
        self.assertTrue(verify_password("new-password", user["password_hash"]))
        self.assertNotIn("password_reset_token_hash", user)
        self.assertNotIn("password_reset_expires_at", user)
        with patch.object(auth, "db", SimpleNamespace(users=FakeUsers(user))):
            with self.assertRaises(HTTPException) as error:
                auth.reset_password(PasswordResetIn(token=token, password="another-password"))
        self.assertEqual(error.exception.status_code, 400)

    def test_reset_password_rejects_expired_token(self):
        token = "expired-reset-token"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        user = {
            "_id": ObjectId(),
            "email": "creator@example.com",
            "password_reset_token_hash": token_hash,
            "password_reset_expires_at": datetime.now(timezone.utc) - timedelta(seconds=1),
        }

        with patch.object(auth, "db", SimpleNamespace(users=FakeUsers(user))):
            with self.assertRaises(HTTPException) as error:
                auth.reset_password(PasswordResetIn(token=token, password="new-password"))

        self.assertEqual(error.exception.status_code, 400)
        self.assertNotIn("password_hash", user)


if __name__ == "__main__":
    unittest.main()
