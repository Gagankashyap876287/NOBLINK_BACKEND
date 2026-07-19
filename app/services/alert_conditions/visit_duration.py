from app.services.alert_conditions.base import EvaluationContext
from app.services.alert_conditions.helpers import (
    candidate,
    threshold_number,
    zone_applies,
)


class VisitDurationEvaluator:
    async def evaluate(
        self,
        rule: dict,
        context: EvaluationContext,
    ) -> list[dict]:
        threshold = threshold_number(rule)
        matches = []

        for visit in context.visits:
            if not zone_applies(rule, visit.get("zone")):
                continue

            if visit["durationMinutes"] > threshold:
                matches.append(candidate(visit, rule))

        return matches
