from app.repositories.workflow_repository import WorkflowRepository
from app.utils.serialize import serialize_document


class WorkflowService:
    

    def __init__(self):
        self.repository = WorkflowRepository()

    async def get_first_step(self, workflow_name: str) -> dict | None:
        workflow = await self.repository.get_by_name(workflow_name)

        if workflow is None:
            return None

        steps = workflow.get("steps") or []

        if not steps:
            return None

        return min(steps, key=lambda step: step["order"])

    async def get_workflow(self, workflow_name: str) -> dict | None:
        workflow = await self.repository.get_by_name(workflow_name)

        if workflow is None:
            return None

        document = serialize_document(workflow)
        document["steps"] = sorted(
            document.get("steps") or [],
            key=lambda step: step["order"],
        )
        return document
