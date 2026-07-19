from datetime import datetime
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId

from app.core.exceptions import BadRequestError


def serialize_document(document: dict | None) -> dict | None:
    if document is None:
        return None

    return {key: serialize_value(value) for key, value in document.items()}


def serialize_documents(documents: list[dict]) -> list[dict]:
    return [serialize_document(document) for document in documents]


def serialize_value(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, list):
        return [serialize_value(item) for item in value]

    if isinstance(value, dict):
        return serialize_document(value)

    return value


def parse_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as exc:
        raise BadRequestError(f"Invalid id: {value}") from exc
