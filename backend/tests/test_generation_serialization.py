import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from bson import ObjectId

from app.api.routes import generations
from app.core.serialization import serialize_mongo_document
from app.models.schemas import GenerationIn


class GenerationSerializationTests(unittest.TestCase):
    def test_serializes_root_and_nested_object_ids(self):
        generation_id = ObjectId()
        nested_id = ObjectId()

        result = serialize_mongo_document(
            {
                "_id": generation_id,
                "metadata": {"source_id": nested_id},
            }
        )

        self.assertEqual(result["id"], str(generation_id))
        self.assertEqual(result["metadata"]["source_id"], str(nested_id))
        self.assertNotIn("_id", result)

    def test_create_returns_json_safe_document_after_insert(self):
        generation_id = ObjectId()

        class FakeCollection:
            def insert_one(self, document):
                document["_id"] = generation_id
                return SimpleNamespace(inserted_id=generation_id)

        with (
            patch.object(generations, "db", SimpleNamespace(generations=FakeCollection())),
            patch.object(generations, "charge", return_value=1),
            patch.object(
                generations,
                "text_generate",
                new=AsyncMock(
                    return_value={
                        "status": "completed",
                        "text": "A generated draft",
                        "model": "test-model",
                    }
                ),
            ),
        ):
            result = asyncio.run(
                generations.create(
                    GenerationIn(kind="text", prompt="Write a welcome message"),
                    {"id": str(ObjectId())},
                )
            )

        self.assertEqual(result["id"], str(generation_id))
        self.assertNotIn("_id", result)
        json.dumps(result)


if __name__ == "__main__":
    unittest.main()
