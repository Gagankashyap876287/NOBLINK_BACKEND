from datetime import datetime

from fastapi import APIRouter, Query

from app.core.exceptions import BadRequestError
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/fleet-summary")
async def fleet_summary():
    service = AnalyticsService()
    return {"success": True, "data": await service.fleet_summary()}


@router.get("/breakdown")
async def breakdown(
    dimension: str = Query(
        ...,
        description="One of: region, alertType, resident, coordinator",
    ),
):
    service = AnalyticsService()

    try:
        data = await service.breakdown(dimension)
    except ValueError as exc:
        raise BadRequestError(str(exc)) from exc

    return {"success": True, "data": data}


@router.get("/sla-breaches")
async def sla_breaches():
    service = AnalyticsService()
    breaches = await service.sla_breaches()
    return {"success": True, "count": len(breaches), "data": breaches}


@router.get("/coordinators")
async def coordinator_performance():
    service = AnalyticsService()
    return {"success": True, "data": await service.coordinator_performance()}


@router.get("/activity")
async def activity_timeline(
    start: datetime = Query(..., description="ISO start datetime"),
    end: datetime = Query(..., description="ISO end datetime"),
):
    if end < start:
        raise BadRequestError("end must be greater than or equal to start.")

    service = AnalyticsService()
    return {
        "success": True,
        "data": await service.activity_timeline(start=start, end=end),
    }
