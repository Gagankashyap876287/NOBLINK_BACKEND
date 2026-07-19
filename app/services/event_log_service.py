from datetime import datetime

from app.repositories.alert_event_log_repository import AlertEventLogRepository
from app.utils.time import utc_now


class EventLogService:

    def __init__(self):
        self.repository = AlertEventLogRepository()

    async def log_alert_created(
        self,
        alert_id,
        timestamp: datetime | None = None,
    ):
        await self.repository.insert(
            {
                "alertId": alert_id,
                "eventType": "ALERT_CREATED",
                "description": "Alert Created",
                "performedBy": "SYSTEM",
                "timestamp": timestamp or utc_now(),
            }
        )

    async def log_visit_opened(
        self,
        visit_id,
        timestamp: datetime | None = None,
    ):
        await self.repository.insert(
            {
                "visitId": visit_id,
                "eventType": "VISIT_OPENED",
                "performedBy": "SYSTEM",
                "timestamp": timestamp or utc_now(),
            }
        )

    async def log_visit_closed(
        self,
        visit_id,
        timestamp: datetime | None = None,
    ):
        await self.repository.insert(
            {
                "visitId": visit_id,
                "eventType": "VISIT_CLOSED",
                "performedBy": "SYSTEM",
                "timestamp": timestamp or utc_now(),
            }
        )
