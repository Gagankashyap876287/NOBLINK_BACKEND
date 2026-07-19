from datetime import datetime


def hours_between(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 3600


def find_workflow_step(workflow: dict | None, step_order: int) -> dict | None:
    if not workflow:
        return None

    return next(
        (
            step
            for step in workflow.get("steps") or []
            if step.get("order") == step_order
        ),
        None,
    )


def is_step_past_sla(
    step_started_at: datetime | None,
    max_response_hours: int | None,
    clock: datetime,
) -> bool:
    if step_started_at is None:
        return False

    limit = max_response_hours or 0

    if limit <= 0:
        return False

    return hours_between(step_started_at, clock) > limit
