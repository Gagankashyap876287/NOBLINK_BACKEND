from bson import ObjectId

from app.database.collections import Collections
from app.utils.serialize import parse_object_id


class AlertEventLogRepository:

    def __init__(self):
        self.collection = Collections.alert_event_logs()

    async def insert(self, document: dict):
        await self.collection.insert_one(document)

    async def find_by_alert_id(self, alert_id) -> list[dict]:
        clauses = [{"alertId": alert_id}]

        if isinstance(alert_id, str):
            clauses.append({"alertId": parse_object_id(alert_id)})
        elif isinstance(alert_id, ObjectId):
            clauses.append({"alertId": str(alert_id)})

        return await self.collection.find(
            {"$or": clauses}
        ).sort("timestamp", 1).to_list(None)

    async def aggregate(self, pipeline: list[dict]) -> list[dict]:
        return await self.collection.aggregate(pipeline).to_list(None)
