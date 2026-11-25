from typing import Any

from bson import ObjectId
from fastapi.encoders import jsonable_encoder


def serialize_mongo_document(document: dict[str, Any]) -> dict[str, Any]:
    serialized = dict(document)
    serialized["id"] = str(serialized.pop("_id"))
    return jsonable_encoder(serialized, custom_encoder={ObjectId: str})
