from app.services.alert_conditions.base import ConditionEvaluator
from app.services.alert_conditions.event_type import EventTypeEvaluator
from app.services.alert_conditions.night_visits import NightVisitsEvaluator
from app.services.alert_conditions.offline import OfflineSensorEvaluator
from app.services.alert_conditions.quiet_gap import QuietGapEvaluator
from app.services.alert_conditions.visit_duration import VisitDurationEvaluator

CONDITION_EVALUATORS: dict[str, ConditionEvaluator] = {
    "visit_duration_minutes_gt": VisitDurationEvaluator(),
    "event_type_is": EventTypeEvaluator(),
    "night_visits_count_gt": NightVisitsEvaluator(),
    "quiet_gap_minutes_gt": QuietGapEvaluator(),
    "no_heartbeat_minutes_gt": OfflineSensorEvaluator(),
}


def get_condition_evaluator(condition: str | None) -> ConditionEvaluator | None:
    if not condition:
        return None

    return CONDITION_EVALUATORS.get(condition)
