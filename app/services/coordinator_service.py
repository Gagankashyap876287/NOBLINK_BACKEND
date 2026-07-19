from datetime import datetime

from app.repositories.alert_repository import AlertRepository
from app.repositories.coordinator_repository import CoordinatorRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.utils.platform_clock import PlatformClock
from app.utils.serialize import serialize_document
from app.utils.sla import find_workflow_step, is_step_past_sla


class CoordinatorService:
    

    def __init__(self):
        self.repository = CoordinatorRepository()
        self.alert_repository = AlertRepository()
        self.workflow_repository = WorkflowRepository()
        self.clock = PlatformClock()

    async def assign(self, region: str):
        coordinators = await self.repository.get_by_region(region)

        if not coordinators:
            return None

        return coordinators[0]

    async def get_coordinator_load(self, coordinator_id: str) -> dict | None:
        coordinator = await self.repository.get_by_coordinator_id(coordinator_id)

        if coordinator is None:
            return None

        clock = await self.clock.now()
        open_alerts = await self.alert_repository.find_many(
            {
                "coordinatorId": coordinator_id,
                "status": "OPEN",
            }
        )

        workflow_cache: dict[str, dict] = {}
        past_sla = 0
        open_risk = 0

        for alert in open_alerts:
            open_risk += alert.get("riskScore") or 0

            if await self._is_past_sla(alert, clock, workflow_cache):
                past_sla += 1

        return {
            "coordinator": serialize_document(coordinator),
            "load": {
                "openAlerts": len(open_alerts),
                "targetOpenCases": coordinator.get("targetOpenCases"),
                "pastSlaCount": past_sla,
                "openRisk": open_risk,
                "asOf": clock,
            },
        }

    async def _is_past_sla(
        self,
        alert: dict,
        clock: datetime,
        workflow_cache: dict[str, dict],
    ) -> bool:
        workflow_name = alert.get("workflow", {}).get("workflowName")
        current_step = alert.get("workflow", {}).get("currentStep")
        step_started_at = alert.get("workflow", {}).get("stepStartedAt")

        if not workflow_name or current_step is None:
            return False

        if workflow_name not in workflow_cache:
            workflow_cache[workflow_name] = await self.workflow_repository.get_by_name(
                workflow_name
            )

        step = find_workflow_step(workflow_cache.get(workflow_name), current_step)
        if step is None:
            return False

        return is_step_past_sla(
            step_started_at,
            step.get("maxResponseHours"),
            clock,
        )
