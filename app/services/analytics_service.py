from datetime import datetime

from app.repositories.alert_event_log_repository import AlertEventLogRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.coordinator_repository import CoordinatorRepository
from app.utils.platform_clock import PlatformClock
from app.utils.serialize import serialize_documents


class AnalyticsService:
    
    def __init__(self):
        self.alert_repository = AlertRepository()
        self.event_log_repository = AlertEventLogRepository()
        self.coordinator_repository = CoordinatorRepository()
        self.clock = PlatformClock()

    async def fleet_summary(self) -> dict:
        clock = await self.clock.now()

        status_pipeline = [
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "totalRisk": {"$sum": "$riskScore"},
                }
            }
        ]
        status_rows = await self.alert_repository.aggregate(status_pipeline)

        by_status = {
            row["_id"]: {
                "count": row["count"],
                "totalRisk": row["totalRisk"],
            }
            for row in status_rows
        }

        totals = await self.alert_repository.aggregate(
            [
                {
                    "$group": {
                        "_id": None,
                        "totalAlerts": {"$sum": 1},
                        "totalRisk": {"$sum": "$riskScore"},
                    }
                }
            ]
        )

        total_alerts = totals[0]["totalAlerts"] if totals else 0
        total_risk = totals[0]["totalRisk"] if totals else 0

        open_risk = by_status.get("OPEN", {}).get("totalRisk", 0)
        breaches = await self.sla_breaches()

        return {
            "asOf": clock,
            "totalAlerts": total_alerts,
            "totalRiskExposure": total_risk,
            "openRiskExposure": open_risk,
            "slaBreachCount": len(breaches),
            "byStatus": {
                "OPEN": by_status.get("OPEN", {"count": 0, "totalRisk": 0}),
                "RESOLVED": by_status.get(
                    "RESOLVED", {"count": 0, "totalRisk": 0}
                ),
                "DISMISSED": by_status.get(
                    "DISMISSED", {"count": 0, "totalRisk": 0}
                ),
            },
        }

    async def breakdown(self, dimension: str) -> dict:
        field_map = {
            "region": "$location.region",
            "alertType": "$alertType",
            "resident": "$resident",
            "coordinator": "$coordinatorId",
        }

        if dimension not in field_map:
            raise ValueError(
                "dimension must be one of: region, alertType, resident, coordinator"
            )

        pipeline = [
            {
                "$group": {
                    "_id": field_map[dimension],
                    "count": {"$sum": 1},
                    "totalRisk": {"$sum": "$riskScore"},
                }
            },
            {"$sort": {"totalRisk": -1}},
            {
                "$project": {
                    "_id": 0,
                    "key": {"$ifNull": ["$_id", "UNASSIGNED"]},
                    "count": 1,
                    "totalRisk": 1,
                }
            },
        ]

        rows = await self.alert_repository.aggregate(pipeline)
        clock = await self.clock.now()

        return {
            "asOf": clock,
            "dimension": dimension,
            "groups": rows,
        }

    async def sla_breaches(self) -> list[dict]:
        
        clock = await self.clock.now()

        pipeline = [
            {"$match": {"status": "OPEN"}},
            {
                "$lookup": {
                    "from": "workflow_configs",
                    "localField": "workflow.workflowName",
                    "foreignField": "workflowName",
                    "as": "workflowConfig",
                }
            },
            {"$unwind": "$workflowConfig"},
            {
                "$addFields": {
                    "currentStepConfig": {
                        "$first": {
                            "$filter": {
                                "input": "$workflowConfig.steps",
                                "as": "step",
                                "cond": {
                                    "$eq": [
                                        "$$step.order",
                                        "$workflow.currentStep",
                                    ]
                                },
                            }
                        }
                    }
                }
            },
            {"$match": {"currentStepConfig": {"$ne": None}}},
            {
                "$addFields": {
                    "hoursOpen": {
                        "$divide": [
                            {
                                "$subtract": [
                                    clock,
                                    "$workflow.stepStartedAt",
                                ]
                            },
                            1000 * 60 * 60,
                        ]
                    },
                    "slaLimitHours": "$currentStepConfig.maxResponseHours",
                }
            },
            {
                "$match": {
                    "$expr": {
                        "$and": [
                            {"$gt": ["$slaLimitHours", 0]},
                            {"$gt": ["$hoursOpen", "$slaLimitHours"]},
                        ]
                    }
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "alertType": 1,
                    "resident": 1,
                    "coordinatorId": 1,
                    "riskScore": 1,
                    "status": 1,
                    "currentStep": "$workflow.currentStep",
                    "currentStepName": "$workflow.currentStepName",
                    "workflowName": "$workflow.workflowName",
                    "hoursOpen": {"$round": ["$hoursOpen", 2]},
                    "slaLimitHours": 1,
                    "hoursOverdue": {
                        "$round": [
                            {"$subtract": ["$hoursOpen", "$slaLimitHours"]},
                            2,
                        ]
                    },
                }
            },
            {"$sort": {"hoursOverdue": -1}},
        ]

        rows = await self.alert_repository.aggregate(pipeline)
        return serialize_documents(rows)

    async def coordinator_performance(self) -> list[dict]:
        clock = await self.clock.now()
        coordinators = await self.coordinator_repository.get_all()
        breaches = await self.sla_breaches()

        breach_counts: dict[str, int] = {}
        for breach in breaches:
            coordinator_id = breach.get("coordinatorId")
            if coordinator_id:
                breach_counts[coordinator_id] = (
                    breach_counts.get(coordinator_id, 0) + 1
                )

        results = []

        for coordinator in coordinators:
            coordinator_id = coordinator.get("coordinatorId")
            open_alerts = await self.alert_repository.find_many(
                {
                    "coordinatorId": coordinator_id,
                    "status": "OPEN",
                }
            )

            open_risk = sum(alert.get("riskScore") or 0 for alert in open_alerts)
            hours_open_values = []

            for alert in open_alerts:
                created_at = alert.get("timing", {}).get("createdAt")
                if isinstance(created_at, datetime):
                    hours_open_values.append(
                        (clock - created_at).total_seconds() / 3600
                    )

            avg_hours_open = (
                round(sum(hours_open_values) / len(hours_open_values), 2)
                if hours_open_values
                else 0
            )
            baseline = coordinator.get("baselineResolutionHours") or 0

            results.append(
                {
                    "coordinatorId": coordinator_id,
                    "name": coordinator.get("name"),
                    "region": coordinator.get("region"),
                    "openAlertCount": len(open_alerts),
                    "targetOpenCases": coordinator.get("targetOpenCases"),
                    "openRisk": open_risk,
                    "breachCount": breach_counts.get(coordinator_id, 0),
                    "avgHoursOpen": avg_hours_open,
                    "baselineResolutionHours": baseline,
                    "avgVsBaselineDelta": round(avg_hours_open - baseline, 2),
                }
            )

        results.sort(key=lambda row: row["openRisk"], reverse=True)
        return results

    async def activity_timeline(
        self,
        start: datetime,
        end: datetime,
    ) -> dict:
        pipeline = [
            {
                "$match": {
                    "timestamp": {
                        "$gte": start,
                        "$lte": end,
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "day": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$timestamp",
                            }
                        },
                        "eventType": "$eventType",
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id.day": 1}},
            {
                "$project": {
                    "_id": 0,
                    "day": "$_id.day",
                    "eventType": "$_id.eventType",
                    "count": 1,
                }
            },
        ]

        rows = await self.event_log_repository.aggregate(pipeline)

        by_day: dict[str, dict] = {}

        for row in rows:
            day = row["day"]
            if day not in by_day:
                by_day[day] = {"day": day, "total": 0, "byEventType": {}}

            by_day[day]["byEventType"][row["eventType"]] = row["count"]
            by_day[day]["total"] += row["count"]

        return {
            "start": start,
            "end": end,
            "series": list(by_day.values()),
        }
