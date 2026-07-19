from datetime import datetime

from app.repositories.sensor_ping_repository import SensorPingRepository
from app.utils.time import utc_now


class PlatformClock:


    def __init__(self):
        self.sensor_ping_repository = SensorPingRepository()

    async def now(self) -> datetime:
        latest = await self.sensor_ping_repository.get_latest_timestamp()
        return latest if latest is not None else utc_now()
