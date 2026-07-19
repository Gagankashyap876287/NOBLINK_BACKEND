"""
Delete all records from the Noblink MongoDB database.

Run from noblink-backend (uses .env MONGO_URI / DB_NAME):

    python -m scripts.clear_db
"""

import asyncio
import sys
from pathlib import Path

# Allow `python -m scripts.clear_db` from noblink-backend root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import settings
from app.database.mongodb import mongodb


async def clear_database() -> None:
    await mongodb.connect()

    db = mongodb.database
    names = await db.list_collection_names()
    before = {name: await db[name].count_documents({}) for name in names}

    if before:
        print(f"Clearing database '{settings.DB_NAME}':")
        for name, count in sorted(before.items()):
            print(f"  {name}: {count} document(s)")
    else:
        print(f"Database '{settings.DB_NAME}' is already empty.")

    await mongodb.client.drop_database(settings.DB_NAME)
    print(f"Dropped database '{settings.DB_NAME}'.")

    await mongodb.disconnect()


def main() -> None:
    asyncio.run(clear_database())


if __name__ == "__main__":
    main()
