from app.database.collections import Collections


class SensorRegistryRepository:

    def __init__(self):
        self.collection = Collections.sensor_registry()

    async def get_by_sensor(self, sensor_id: str):
        return await self.collection.find_one({"sensorId": sensor_id})
