from bson import ObjectId

from app.database.collections import Collections
from app.utils.serialize import parse_object_id


class VisitRepository:

    def __init__(self):
        self.collection = Collections.visits()

    async def bulk_insert(self, visits: list[dict]) -> list:
        if not visits:
            return []

        result = await self.collection.insert_many(visits)
        return result.inserted_ids

    async def get_by_id(self, visit_id) -> dict | None:
        if visit_id is None:
            return None

        if isinstance(visit_id, str):
            visit_id = parse_object_id(visit_id)
        elif not isinstance(visit_id, ObjectId):
            return None

        return await self.collection.find_one({"_id": visit_id})

    async def find_by_sensor(self, sensor_id: str) -> list[dict]:
        return await self.collection.find(
            {"sensorId": sensor_id}
        ).sort("entryTime", -1).to_list(None)

    async def find_by_resident(self, resident: str) -> list[dict]:
        return await self.collection.find(
            {"resident": resident}
        ).sort("entryTime", -1).to_list(None)
