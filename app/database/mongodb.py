import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

logger = logging.getLogger("noblink")


class MongoDB:

    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.database: AsyncIOMotorDatabase | None = None

    async def connect(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        await self.client.admin.command("ping")
        self.database = self.client[settings.DB_NAME]
        await self._ensure_indexes()
        logger.info("Connected to MongoDB database: %s", settings.DB_NAME)

    async def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    async def _ensure_indexes(self):
        
        await self.database.sensor_pings.create_index(
            [("sensorId", 1), ("timestamp", 1), ("eventType", 1)],
            unique=True,
            name="uniq_ping",
        )
        await self.database.sensor_pings.create_index(
            [("timestamp", -1)],
            name="ping_timestamp_desc",
        )
        await self.database.sensor_registry.create_index(
            "sensorId",
            unique=True,
            name="uniq_sensor",
        )
        await self.database.visits.create_index(
            [("sensorId", 1), ("entryTime", -1)],
            name="visits_by_sensor",
        )
        await self.database.visits.create_index(
            [("resident", 1), ("entryTime", -1)],
            name="visits_by_resident",
        )
        await self.database.alerts.create_index(
            [("status", 1), ("coordinatorId", 1), ("timing.createdAt", -1)],
            name="alerts_list",
        )
        await self.database.alerts.create_index(
            [("location.region", 1), ("alertType", 1)],
            name="alerts_breakdown",
        )
        await self.database.workflow_configs.create_index(
            "workflowName",
            unique=True,
            name="uniq_workflow",
        )
        await self.database.coordinators.create_index(
            "coordinatorId",
            unique=True,
            name="uniq_coordinator",
        )
        await self.database.alert_event_logs.create_index(
            [("alertId", 1), ("timestamp", 1)],
            name="events_by_alert",
        )
        await self.database.alert_event_logs.create_index(
            [("timestamp", 1), ("eventType", 1)],
            name="events_timeline",
        )


mongodb = MongoDB()
