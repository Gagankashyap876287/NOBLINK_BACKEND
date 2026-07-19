from app.database.collections import Collections


class WorkflowRepository:

    def __init__(self):
        self.collection = Collections.workflow_configs()

    async def get_by_name(self, workflow_name: str):
        return await self.collection.find_one({"workflowName": workflow_name})
