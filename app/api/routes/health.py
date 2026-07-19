from fastapi import APIRouter

from app.database.mongodb import mongodb
from app.utils.platform_clock import PlatformClock

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health():
    db_ok = False

    try:
        await mongodb.client.admin.command("ping")
        db_ok = True
    except Exception:
        db_ok = False

    as_of = None
    if db_ok:
        as_of = await PlatformClock().now()

    return {
        "success": True,
        "status": "ok" if db_ok else "degraded",
        "database": "up" if db_ok else "down",
        "asOf": as_of,
    }
