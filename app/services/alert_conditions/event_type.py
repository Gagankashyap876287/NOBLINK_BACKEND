from app.services.alert_conditions.base import EvaluationContext
from app.services.alert_conditions.helpers import (
    candidate,
    threshold_text,
    zone_applies,
)


class EventTypeEvaluator:
    async def evaluate(
        self,
        rule: dict,
        context: EvaluationContext,
    ) -> list[dict]:
        target = threshold_text(rule)
        matches = []

        for visit in context.visits:
            if not zone_applies(rule, visit.get("zone")):
                continue

            if target in visit.get("triggerEvents", []):
                matches.append(candidate(visit, rule))

        return matches
