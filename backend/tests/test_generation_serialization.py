import unittest

from bson import ObjectId

from app.core.serialization import serialize_mongo_document


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


if __name__ == "__main__":
    unittest.main()
