from fastapi import APIRouter, Query

from app.services.visit_service import VisitService

router = APIRouter(prefix="/visits", tags=["Visits"])


@router.get("")
async def get_visit_history(
    sensorId: str | None = Query(default=None),
    resident: str | None = Query(default=None),
):
    service = VisitService()
    visits = await service.get_visit_history(
        sensor_id=sensorId,
        resident=resident,
    )
    return {"success": True, "count": len(visits), "data": visits}
