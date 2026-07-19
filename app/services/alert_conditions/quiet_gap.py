from collections import defaultdict
from datetime import datetime

from app.enums.event_type import EventType
from app.services.alert_conditions.base import EvaluationContext
from app.services.alert_conditions.helpers import (
    candidate,
    threshold_number,
    zone_applies,
)

ACTIVITY_EVENT_TYPES = {
    EventType.PRESENCE.value,
    EventType.MOTION.value,
}


class QuietGapEvaluator:

    async def evaluate(
        self,
        rule: dict,
        context: EvaluationContext,
    ) -> list[dict]:
        threshold_minutes = threshold_number(rule)
        activity_by_sensor: dict[str, list[dict]] = defaultdict(list)
        all_sensor_ids: set[str] = set()

        for ping in context.sensor_pings:
            sensor_id = ping["sensorId"]
            all_sensor_ids.add(sensor_id)

            event_type = ping["eventType"]
            if hasattr(event_type, "value"):
                event_type = event_type.value

            if event_type in ACTIVITY_EVENT_TYPES:
                activity_by_sensor[sensor_id].append(ping)

        matches: list[dict] = []

        for sensor_id in sorted(all_sensor_ids):
            activity = sorted(
                activity_by_sensor.get(sensor_id, []),
                key=lambda item: item["timestamp"],
            )

            for index in range(len(activity) - 1):
                previous = activity[index]
                nxt = activity[index + 1]
                gap_minutes = (
                    nxt["timestamp"] - previous["timestamp"]
                ).total_seconds() / 60

                if gap_minutes > threshold_minutes:
                    visit_context = await self._context_for_sensor(
                        sensor_id,
                        context,
                        silence_after=previous["timestamp"],
                    )
                    if visit_context is None:
                        continue
                    if not zone_applies(rule, visit_context.get("zone")):
                        continue
                    matches.append(candidate(visit_context, rule))

            # Silence from last activity (or first ping if never active) to "now"
            if context.clock is None:
                continue

            if activity:
                anchor = activity[-1]["timestamp"]
            else:
                sensor_pings = [
                    ping
                    for ping in context.sensor_pings
                    if ping["sensorId"] == sensor_id
                ]
                if not sensor_pings:
                    continue
                anchor = min(ping["timestamp"] for ping in sensor_pings)

            ongoing = (context.clock - anchor).total_seconds() / 60

            if ongoing > threshold_minutes:
                visit_context = await self._context_for_sensor(
                    sensor_id,
                    context,
                    silence_after=anchor,
                )
                if visit_context is None:
                    continue
                if not zone_applies(rule, visit_context.get("zone")):
                    continue
                matches.append(candidate(visit_context, rule))

        return matches

    async def _context_for_sensor(
        self,
        sensor_id: str,
        context: EvaluationContext,
        silence_after: datetime,
    ) -> dict | None:
        """
        Build alert location/workflow context without requiring an active visit.
        Prefer the latest visit for the sensor; otherwise use the registry.
        """
        latest_visit = None

        for visit in context.visits:
            if visit.get("sensorId") != sensor_id:
                continue
            if latest_visit is None or visit["entryTime"] > latest_visit["entryTime"]:
                latest_visit = visit

        if latest_visit is not None:
            return {
                **latest_visit,
                # Anchor alert timing to when silence was last broken
                "lastPingTime": silence_after,
                "entryTime": silence_after,
            }

        repository = context.sensor_registry_repository
        if repository is None:
            return None

        registry = await repository.get_by_sensor(sensor_id)
        if registry is None:
            return None

        return {
            "_id": None,
            "sensorId": sensor_id,
            "resident": registry["resident"]["name"],
            "room": registry["room"],
            "zone": registry["zone"],
            "facility": registry["facility"],
            "region": registry["region"],
            "workflowName": registry["workflowName"],
            "lastPingTime": silence_after,
            "entryTime": silence_after,
        }
