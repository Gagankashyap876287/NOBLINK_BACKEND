from fastapi import APIRouter

from app.core.exceptions import NotFoundError
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.get("/{workflow_name}")
async def get_workflow(workflow_name: str):
    service = WorkflowService()
    workflow = await service.get_workflow(workflow_name)

    if workflow is None:
        raise NotFoundError("Workflow not found.")

    return {"success": True, "data": workflow}
