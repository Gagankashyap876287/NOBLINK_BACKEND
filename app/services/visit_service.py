from collections import defaultdict
from datetime import timedelta

from app.core.constants import VISIT_INACTIVITY_MINUTES
from app.core.exceptions import BadRequestError
from app.enums.event_type import EventType
from app.models.visit import VisitModel
from app.repositories.sensor_registry_repository import SensorRegistryRepository
from app.repositories.visit_repository import VisitRepository
from app.services.event_log_service import EventLogService
from app.utils.serialize import serialize_documents
from app.utils.time import utc_now

VISIT_EVENT_TYPES = {
    EventType.PRESENCE.value,
    EventType.MOTION.value,
    EventType.FALL_SUSPECTED.value,
}


class VisitService:

    def __init__(self):
        self.visit_repository = VisitRepository()
        self.sensor_registry_repository = SensorRegistryRepository()
        self.event_log_service = EventLogService()


    async def get_visit_history(
        self,
        sensor_id: str | None = None,
        resident: str | None = None,
    ) -> list[dict]:
        if not sensor_id and not resident:
            raise BadRequestError("Provide sensorId and/or resident.")

        if sensor_id and resident:
            sensor_visits = await self.visit_repository.find_by_sensor(sensor_id)
            visits = [
                visit
                for visit in sensor_visits
                if visit.get("resident") == resident
            ]
        elif sensor_id:
            visits = await self.visit_repository.find_by_sensor(sensor_id)
        else:
            visits = await self.visit_repository.find_by_resident(resident)

        return serialize_documents(visits)


    async def generate_and_save_visits(
        self,
        sensor_pings: list[dict],
    ) -> list[dict]:
        if not sensor_pings:
            return []

        grouped: dict[str, list[dict]] = defaultdict(list)

        for ping in sensor_pings:
            event_type = ping["eventType"]
            if hasattr(event_type, "value"):
                event_type = event_type.value

            if event_type not in VISIT_EVENT_TYPES:
                continue

            grouped[ping["sensorId"]].append({**ping, "eventType": event_type})

        visits: list[dict] = []

        for sensor_id, pings in grouped.items():
            pings.sort(key=lambda item: item["timestamp"])

            registry = await self.sensor_registry_repository.get_by_sensor(
                sensor_id
            )

            if registry is None:
                continue

            current_visit = None

            for ping in pings:
                if current_visit is None:
                    current_visit = self._create_visit(ping, registry)
                    continue

                gap = ping["timestamp"] - current_visit["lastPingTime"]

                if gap <= timedelta(minutes=VISIT_INACTIVITY_MINUTES):
                    current_visit["lastPingTime"] = ping["timestamp"]
                    current_visit["pingCount"] += 1

                    if ping["eventType"] not in current_visit["triggerEvents"]:
                        current_visit["triggerEvents"].append(ping["eventType"])
                else:
                    visits.append(self._close_visit(current_visit))
                    current_visit = self._create_visit(ping, registry)

            if current_visit:
                visits.append(self._close_visit(current_visit))

        models: list[dict] = []

        for visit in visits:
            models.append(VisitModel(**visit).model_dump())

        inserted_ids = await self.visit_repository.bulk_insert(models)

        for visit, visit_id in zip(models, inserted_ids):
            visit["_id"] = visit_id
            await self.event_log_service.log_visit_opened(
                visit_id,
                timestamp=visit["entryTime"],
            )
            await self.event_log_service.log_visit_closed(
                visit_id,
                timestamp=visit["exitTime"] or visit["lastPingTime"],
            )

        return models

    def _create_visit(self, ping: dict, registry: dict) -> dict:
        return {
            "sensorId": ping["sensorId"],
            "resident": registry["resident"]["name"],
            "room": registry["room"],
            "zone": registry["zone"],
            "facility": registry["facility"],
            "region": registry["region"],
            "workflowName": registry["workflowName"],
            "entryTime": ping["timestamp"],
            "lastPingTime": ping["timestamp"],
            "exitTime": None,
            "durationMinutes": 0,
            "pingCount": 1,
            "autoExited": True,
            "triggerEvents": [ping["eventType"]],
            "createdAt": utc_now(),
        }

    def _close_visit(self, visit: dict) -> dict:
        # Auto-exit at the inactivity boundary after the last activity ping.
        visit["exitTime"] = visit["lastPingTime"] + timedelta(
            minutes=VISIT_INACTIVITY_MINUTES
        )
        elapsed_seconds = (visit["exitTime"] - visit["entryTime"]).total_seconds()
        visit["durationMinutes"] = max(0.0, round(elapsed_seconds / 60, 2))
        visit["autoExited"] = True
        return visit
