from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


@dataclass
class EvaluationContext:
    visits: list[dict]
    sensor_pings: list[dict]
    clock: datetime | None
    sensor_registry_repository: Any = None


class ConditionEvaluator(Protocol):
    """Interface only — real logic lives in visit_duration, quiet_gap, etc."""

    async def evaluate(
        self,
        rule: dict,
        context: EvaluationContext,
    ) -> list[dict]:
        pass
