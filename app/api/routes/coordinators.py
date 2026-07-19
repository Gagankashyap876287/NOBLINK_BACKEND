from fastapi import APIRouter

from app.core.exceptions import NotFoundError
from app.services.coordinator_service import CoordinatorService

router = APIRouter(prefix="/coordinators", tags=["Coordinators"])


@router.get("/{coordinator_id}")
async def get_coordinator_load(coordinator_id: str):
    service = CoordinatorService()
    result = await service.get_coordinator_load(coordinator_id)

    if result is None:
        raise NotFoundError("Coordinator not found.")

    return {"success": True, "data": result}
