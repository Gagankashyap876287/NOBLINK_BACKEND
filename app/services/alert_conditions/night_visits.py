from collections import defaultdict

from app.services.alert_conditions.base import EvaluationContext
from app.services.alert_conditions.helpers import (
    candidate,
    is_night,
    night_bucket,
    threshold_number,
    zone_applies,
)


class NightVisitsEvaluator:
    async def evaluate(
        self,
        rule: dict,
        context: EvaluationContext,
    ) -> list[dict]:
        threshold = threshold_number(rule)
        buckets: dict[tuple, list[dict]] = defaultdict(list)

        for visit in context.visits:
            if not zone_applies(rule, visit.get("zone")):
                continue

            if not is_night(visit["entryTime"]):
                continue

            key = (
                visit["resident"],
                visit["sensorId"],
                night_bucket(visit["entryTime"]),
            )
            buckets[key].append(visit)

        matches = []

        for night_visits in buckets.values():
            if len(night_visits) > threshold:
                anchor = max(night_visits, key=lambda item: item["entryTime"])
                matches.append(candidate(anchor, rule))

        return matches
