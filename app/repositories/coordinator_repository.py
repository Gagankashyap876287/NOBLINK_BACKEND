from app.database.collections import Collections


class CoordinatorRepository:

    def __init__(self):
        self.collection = Collections.coordinators()

    async def get_by_region(self, region: str):
        return await self.collection.find(
            {"region": region, "active": True}
        ).to_list(None)

    async def get_by_coordinator_id(self, coordinator_id: str) -> dict | None:
        return await self.collection.find_one({"coordinatorId": coordinator_id})

    async def get_all(self) -> list[dict]:
        return await self.collection.find().to_list(None)
