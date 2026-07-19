class UploadRepository:

    async def replace(self, collection, documents: list[dict]) -> int:
        await collection.delete_many({})

        if documents:
            await collection.insert_many(documents)

        return len(documents)
