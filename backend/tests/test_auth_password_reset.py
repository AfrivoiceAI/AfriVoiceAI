import hashlib
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from bson import ObjectId
from fastapi import HTTPException

from app.api.routes import auth
from app.core.security import verify_password
from app.models.schemas import (
    PasswordResetIn,
    PasswordResetRequestIn,
    RecoveryQuestionLookupIn,
    RecoveryQuestionResetIn,
    RegisterIn,
)


class FakeUsers:
    def __init__(self, user=None):
        self.user = user

    def find_one(self, query, projection=None):
        if not self.user:
            return None
        if query.get("email") == self.user.get("email"):
            return self.user
        if query.get("_id") == self.user.get("_id"):
            return self.user
        return None

    def insert_one(self, document):
        self.user = document
        self.user["_id"] = ObjectId()
        return SimpleNamespace(inserted_id=self.user["_id"])

    def update_one(self, query, update):
        if not self.user or (
            "_id" in query and query["_id"] != self.user.get("_id")
        ):
            return SimpleNamespace(matched_count=0)

        for field in ("email", "password_reset_token_hash", "recovery_answer_hash"):
            if field in query and self.user.get(field) != query[field]:
                return SimpleNamespace(matched_count=0)
        for field, condition in query.items():
            if not isinstance(condition, dict):
                continue
            value = self.user.get(field)
            if "$gt" in condition and (value is None or value <= condition["$gt"]):
                return SimpleNamespace(matched_count=0)
            if "$lte" in condition and (value is None or value > condition["$lte"]):
                return SimpleNamespace(matched_count=0)
        if "$or" in query:
            matched = False
            for clause in query["$or"]:
                field, condition = next(iter(clause.items()))
                value = self.user.get(field)
                if "$exists" in condition and (field in self.user) == condition["$exists"]:
                    matched = True
                if "$lte" in condition and value is not None and value <= condition["$lte"]:
                    matched = True
            if not matched:
                return SimpleNamespace(matched_count=0)

        self.user.update(update.get("$set", {}))
        for field, amount in update.get("$inc", {}).items():
            self.user[field] = self.user.get(field, 0) + amount
        for field in update.get("$unset", {}):
            self.user.pop(field, None)
        return SimpleNamespace(matched_count=1)


class PasswordResetTests(unittest.TestCase):
    def test_registration_hashes_recovery_answer(self):
        users = FakeUsers()
        with patch.object(auth, "db", SimpleNamespace(users=users)):
            result = auth.register(
                RegisterIn(
                    email="creator@example.com",
                    password="account-password",
                    display_name="Creator",
                    recovery_question="What was my first creative project?",
                    recovery_answer="  Purple   Mango  Sunrise ",
                )
            )

        self.assertTrue(result["user"]["has_recovery_question"])
        self.assertNotIn("recovery_answer", users.user)
        self.assertTrue(
            verify_password(
                "purple mango sunrise",
                users.user["recovery_answer_hash"],
            )
        )

    def test_recovery_question_is_returned_without_answer_hash(self):
        users = FakeUsers(
            {
                "_id": ObjectId(),
                "email": "creator@example.com",
                "recovery_question": "What was my first creative project?",
                "recovery_answer_hash": auth.hash_password("private recovery phrase"),
            }
        )
        with patch.object(auth, "db", SimpleNamespace(users=users)):
            result = auth.get_recovery_question(
                RecoveryQuestionLookupIn(email="creator@example.com")
            )

        self.assertEqual(result, {"question": "What was my first creative project?"})

    def test_question_reset_accepts_normalized_answer_and_updates_password(self):
        user = {
            "_id": ObjectId(),
            "email": "creator@example.com",
            "password_hash": auth.hash_password("old-password"),
            "recovery_question": "What was my first creative project?",
            "recovery_answer_hash": auth.hash_password("purple mango sunrise"),
            "recovery_failed_attempts": 2,
            "password_reset_token_hash": "old-email-reset-token",
        }
        with patch.object(auth, "db", SimpleNamespace(users=FakeUsers(user))):
            result = auth.reset_password_with_question(
                RecoveryQuestionResetIn(
                    email="creator@example.com",
                    answer=" Purple   Mango Sunrise ",
                    password="new-password",
                )
            )

        self.assertEqual(result["message"], "Password reset successfully. You can now sign in.")
        self.assertTrue(verify_password("new-password", user["password_hash"]))
        self.assertNotIn("recovery_answer", user)
        self.assertTrue(
            verify_password("purple mango sunrise", user["recovery_answer_hash"])
        )
        self.assertNotIn("recovery_failed_attempts", user)
        self.assertNotIn("password_reset_token_hash", user)

    def test_question_reset_throttles_repeated_wrong_answers(self):
        user = {
            "_id": ObjectId(),
            "email": "creator@example.com",
            "password_hash": auth.hash_password("old-password"),
            "recovery_question": "What was my first creative project?",
            "recovery_answer_hash": auth.hash_password("private recovery phrase"),
        }
        with patch.object(auth, "db", SimpleNamespace(users=FakeUsers(user))):
            for _ in range(auth.RECOVERY_ATTEMPT_LIMIT - 1):
                with self.assertRaises(HTTPException) as error:
                    auth.reset_password_with_question(
                        RecoveryQuestionResetIn(
                            email="creator@example.com",
                            answer="incorrect phrase",
                            password="new-password",
                        )
                    )
                self.assertEqual(error.exception.status_code, 400)

            with self.assertRaises(HTTPException) as error:
                auth.reset_password_with_question(
                    RecoveryQuestionResetIn(
                        email="creator@example.com",
                        answer="incorrect phrase",
                        password="new-password",
                    )
                )
            self.assertEqual(error.exception.status_code, 429)

            with self.assertRaises(HTTPException) as error:
                auth.reset_password_with_question(
                    RecoveryQuestionResetIn(
                        email="creator@example.com",
                        answer="incorrect phrase",
                        password="new-password",
                    )
                )
            self.assertEqual(error.exception.status_code, 429)

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
