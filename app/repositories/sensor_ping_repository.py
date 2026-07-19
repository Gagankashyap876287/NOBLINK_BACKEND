from app.database.collections import Collections


class SensorPingRepository:

    def __init__(self):
        self.collection = Collections.sensor_pings()

    @staticmethod
    def _ping_key(document: dict) -> tuple:
        event_type = document["eventType"]
        if hasattr(event_type, "value"):
            event_type = event_type.value
        return (document["sensorId"], document["timestamp"], event_type)

    async def all_exist(self, documents: list[dict]) -> bool:
        """True when every uploaded ping is already in the database."""
        if not documents:
            return False

        incoming = {self._ping_key(document) for document in documents}
        sensor_ids = list({sensor_id for sensor_id, _, _ in incoming})

        existing_docs = await self.collection.find(
            {"sensorId": {"$in": sensor_ids}},
            {"sensorId": 1, "timestamp": 1, "eventType": 1},
        ).to_list(None)

        existing = {self._ping_key(document) for document in existing_docs}
        return incoming.issubset(existing)

    async def bulk_upsert(self, documents: list[dict]):
        if not documents:
            return 0

        from pymongo import UpdateOne

        operations = []

        for document in documents:
            event_type = document["eventType"]
            if hasattr(event_type, "value"):
                event_type = event_type.value

            operations.append(
                UpdateOne(
                    {
                        "sensorId": document["sensorId"],
                        "timestamp": document["timestamp"],
                        "eventType": event_type,
                    },
                    {"$setOnInsert": document},
                    upsert=True,
                )
            )

        result = await self.collection.bulk_write(operations, ordered=False)
        return result.upserted_count

    async def get_latest_timestamp(self):
        document = await self.collection.find_one(
            sort=[("timestamp", -1)],
            projection={"timestamp": 1},
        )

        if document is None:
            return None

        return document.get("timestamp")
