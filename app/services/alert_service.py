from datetime import datetime

from app.models.alert import AlertModel
from app.repositories.alert_repository import AlertRepository
from app.repositories.alert_rule_repository import AlertRuleRepository
from app.repositories.alert_event_log_repository import AlertEventLogRepository
from app.repositories.sensor_registry_repository import SensorRegistryRepository
from app.repositories.visit_repository import VisitRepository
from app.services.alert_conditions import EvaluationContext, get_condition_evaluator
from app.services.coordinator_service import CoordinatorService
from app.services.event_log_service import EventLogService
from app.services.workflow_service import WorkflowService
from app.utils.platform_clock import PlatformClock
from app.utils.serialize import serialize_document, serialize_documents
from app.utils.sla import hours_between
from app.utils.time import utc_now


class AlertService:

    def __init__(self):
        self.alert_repository = AlertRepository()
        self.rule_repository = AlertRuleRepository()
        self.sensor_registry_repository = SensorRegistryRepository()
        self.visit_repository = VisitRepository()
        self.event_log_repository = AlertEventLogRepository()
        self.workflow_service = WorkflowService()
        self.coordinator_service = CoordinatorService()
        self.event_log_service = EventLogService()
        self.clock = PlatformClock()

    async def list_alerts(
        self,
        coordinator_id: str | None = None,
        status: str | None = None,
        region: str | None = None,
        resident: str | None = None,
        alert_type: str | None = None,
    ) -> list[dict]:
        filters: dict = {}

        if coordinator_id:
            filters["coordinatorId"] = coordinator_id
        if status:
            filters["status"] = status
        if region:
            filters["location.region"] = region
        if resident:
            filters["resident"] = resident
        if alert_type:
            filters["alertType"] = alert_type

        alerts = await self.alert_repository.find_many(
            filters,
            sort=[("timing.createdAt", -1)],
        )

        clock = await self.clock.now()
        enriched = [self._enrich_alert_summary(alert, clock) for alert in alerts]
        return serialize_documents(enriched)

    async def get_alert_detail(self, alert_id: str) -> dict | None:
        alert = await self.alert_repository.get_by_id(alert_id)

        if alert is None:
            return None

        clock = await self.clock.now()
        visit = None

        if alert.get("visitId") is not None:
            visit = await self.visit_repository.get_by_id(alert["visitId"])

        events = await self.event_log_repository.find_by_alert_id(alert["_id"])

        return {
            "alert": serialize_document(self._enrich_alert_summary(alert, clock)),
            "visit": serialize_document(visit),
            "eventLog": serialize_documents(events),
        }

    def _enrich_alert_summary(self, alert: dict, clock: datetime) -> dict:
        step_started = alert.get("workflow", {}).get("stepStartedAt")
        created_at = alert.get("timing", {}).get("createdAt")

        alert["hoursOnCurrentStep"] = (
            round(hours_between(step_started, clock), 2)
            if isinstance(step_started, datetime)
            else None
        )
        alert["hoursOpen"] = (
            round(hours_between(created_at, clock), 2)
            if isinstance(created_at, datetime)
            else None
        )
        alert["asOf"] = clock
        return alert

    async def generate_and_save_alerts(
        self,
        visits: list[dict],
        sensor_pings: list[dict] | None = None,
    ) -> list[dict]:
        rules = await self.rule_repository.get_enabled_rules()

        if not rules:
            return []

        sensor_pings = sensor_pings or []
        clock = self._resolve_clock(visits, sensor_pings)
        context = EvaluationContext(
            visits=visits,
            sensor_pings=sensor_pings,
            clock=clock,
            sensor_registry_repository=self.sensor_registry_repository,
        )

        candidates: list[dict] = []

        for rule in rules:
            evaluator = get_condition_evaluator(rule.get("condition"))

            if evaluator is None:
                continue

            matches = await evaluator.evaluate(rule, context)
            candidates.extend(matches)

        alerts: list[dict] = []

        for candidate in candidates:
            alert_doc = await self._build_alert(candidate, clock)

            if alert_doc is not None:
                alerts.append(alert_doc)

        inserted_ids = await self.alert_repository.bulk_insert(alerts)

        for alert, alert_id in zip(alerts, inserted_ids or []):
            alert["_id"] = alert_id
            await self.event_log_service.log_alert_created(
                alert_id,
                timestamp=alert["timing"]["createdAt"],
            )

        return alerts

    async def _build_alert(
        self,
        candidate: dict,
        clock: datetime | None,
    ) -> dict | None:
        visit = candidate["visit"]
        rule = candidate["rule"]
        workflow_name = visit.get("workflowName")

        if not workflow_name:
            return None

        first_step = await self.workflow_service.get_first_step(workflow_name)

        if first_step is None:
            return None

        coordinator = await self.coordinator_service.assign(visit["region"])
        coordinator_id = None

        if coordinator is not None:
            coordinator_id = coordinator.get("coordinatorId") or coordinator.get(
                "_id"
            )

        raised_at = (
            visit.get("lastPingTime")
            or visit.get("entryTime")
            or clock
            or utc_now()
        )

        model = AlertModel(
            visitId=visit.get("_id"),
            sensorId=visit["sensorId"],
            resident=visit["resident"],
            coordinatorId=coordinator_id,
            ruleId=rule.get("ruleId"),
            alertType=rule["alertType"],
            severity=rule["baseSeverity"],
            riskScore=rule["baseSeverity"],
            status="OPEN",
            workflow={
                "workflowName": workflow_name,
                "currentStep": first_step["order"],
                "currentStepName": first_step["stepName"],
                "stepStartedAt": raised_at,
            },
            location={
                "region": visit["region"],
                "facility": visit["facility"],
                "room": visit["room"],
                "zone": visit.get("zone"),
            },
            timing={
                "createdAt": raised_at,
                "updatedAt": raised_at,
                "resolvedAt": None,
            },
        )

        return model.model_dump()

    def _resolve_clock(
        self,
        visits: list[dict],
        sensor_pings: list[dict],
    ) -> datetime | None:
        candidates: list[datetime] = []

        for ping in sensor_pings:
            candidates.append(ping["timestamp"])

        for visit in visits:
            candidates.append(visit["lastPingTime"])

        if not candidates:
            return None

        return max(candidates)
