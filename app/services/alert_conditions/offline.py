from datetime import datetime

from app.services.alert_conditions.base import EvaluationContext
from app.services.alert_conditions.helpers import (
    candidate,
    threshold_number,
    zone_applies,
)


class OfflineSensorEvaluator:
    async def evaluate(
        self,
        rule: dict,
        context: EvaluationContext,
    ) -> list[dict]:
        if context.clock is None:
            return []

        threshold_minutes = threshold_number(rule)
        last_ping_by_sensor: dict[str, datetime] = {}

        for ping in context.sensor_pings:
            sensor_id = ping["sensorId"]
            timestamp = ping["timestamp"]
            previous = last_ping_by_sensor.get(sensor_id)

            if previous is None or timestamp > previous:
                last_ping_by_sensor[sensor_id] = timestamp

        for visit in context.visits:
            sensor_id = visit["sensorId"]
            timestamp = visit["lastPingTime"]
            previous = last_ping_by_sensor.get(sensor_id)

            if previous is None or timestamp > previous:
                last_ping_by_sensor[sensor_id] = timestamp

        visit_by_sensor: dict[str, dict] = {}

        for visit in context.visits:
            sensor_id = visit["sensorId"]
            existing = visit_by_sensor.get(sensor_id)

            if existing is None or visit["entryTime"] > existing["entryTime"]:
                visit_by_sensor[sensor_id] = visit

        matches = []

        for sensor_id, last_seen in last_ping_by_sensor.items():
            silent_minutes = (context.clock - last_seen).total_seconds() / 60

            if silent_minutes <= threshold_minutes:
                continue

            visit_context = visit_by_sensor.get(sensor_id)

            if visit_context is None:
                visit_context = await self._context_from_registry(
                    sensor_id,
                    context,
                )

                if visit_context is None:
                    continue

            if not zone_applies(rule, visit_context.get("zone")):
                continue

            matches.append(candidate(visit_context, rule))

        return matches

    async def _context_from_registry(
        self,
        sensor_id: str,
        context: EvaluationContext,
    ) -> dict | None:
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
        }
