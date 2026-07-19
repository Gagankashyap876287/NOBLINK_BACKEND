from fastapi import APIRouter, Query

from app.core.exceptions import NotFoundError
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("")
async def list_alerts(
    coordinatorId: str | None = Query(default=None),
    status: str | None = Query(default=None),
    region: str | None = Query(default=None),
    resident: str | None = Query(default=None),
    alertType: str | None = Query(default=None),
):
    service = AlertService()
    alerts = await service.list_alerts(
        coordinator_id=coordinatorId,
        status=status,
        region=region,
        resident=resident,
        alert_type=alertType,
    )
    return {"success": True, "count": len(alerts), "data": alerts}


@router.get("/{alert_id}")
async def get_alert_detail(alert_id: str):
    service = AlertService()
    detail = await service.get_alert_detail(alert_id)

    if detail is None:
        raise NotFoundError("Alert not found.")

    return {"success": True, "data": detail}
