from app.database.collections import Collections
from app.utils.serialize import parse_object_id


class AlertRepository:

    def __init__(self):
        self.collection = Collections.alerts()

    async def bulk_insert(self, alerts: list[dict]):
        if not alerts:
            return []

        result = await self.collection.insert_many(alerts)
        return result.inserted_ids

    async def find_many(
        self,
        filters: dict | None = None,
        sort: list[tuple] | None = None,
    ) -> list[dict]:
        cursor = self.collection.find(filters or {})

        if sort:
            cursor = cursor.sort(sort)

        return await cursor.to_list(None)

    async def get_by_id(self, alert_id: str) -> dict | None:
        object_id = parse_object_id(alert_id)
        return await self.collection.find_one({"_id": object_id})

    async def aggregate(self, pipeline: list[dict]) -> list[dict]:
        return await self.collection.aggregate(pipeline).to_list(None)
