from fastapi import APIRouter

from app.api.routes.alerts import router as alerts_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.coordinators import router as coordinators_router
from app.api.routes.health import router as health_router
from app.api.routes.upload import router as upload_router
from app.api.routes.visits import router as visits_router
from app.api.routes.workflows import router as workflows_router

router = APIRouter()

router.include_router(health_router)
router.include_router(upload_router)
router.include_router(alerts_router)
router.include_router(visits_router)
router.include_router(workflows_router)
router.include_router(coordinators_router)
router.include_router(analytics_router)
