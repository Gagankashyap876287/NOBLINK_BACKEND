from fastapi import APIRouter, File, UploadFile

from app.schemas.upload_response import SensorPingUploadResponse, UploadResponse
from app.services.config_export_service import ConfigExportService
from app.services.upload_service import SensorPingUploadService, UploadService

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.get(
    "/config-status",
    summary="Config upload status",
)
async def config_status():
 
    return await ConfigExportService().status()


@router.get(
    "/export/{config_key}",
    summary="Export uploaded config as CSV",
)
async def export_config(config_key: str):
    
    
    return await ConfigExportService().export_csv(config_key)


@router.post(
    "/sensor-registry",
    response_model=UploadResponse,
    summary="Upload Sensor Registry",
)
async def upload_sensor_registry(file: UploadFile = File(...)):
    """Replace sensor_registry with CSV rows (Sensor_ID → resident/zone/workflow)."""
    return await UploadService().upload_sensor_registry(file)


@router.post(
    "/sensor-pings",
    response_model=SensorPingUploadResponse,
    summary="Upload Sensor Pings",
)
async def upload_sensor_pings(file: UploadFile = File(...)):
   
    return await SensorPingUploadService().upload(file)


@router.post(
    "/alert-rules",
    response_model=UploadResponse,
    summary="Upload Alert Rules",
)
async def upload_alert_rules(file: UploadFile = File(...)):
   
    return await UploadService().upload_alert_rules(file)


@router.post(
    "/workflow-configs",
    response_model=UploadResponse,
    summary="Upload Workflow Configs",
)
async def upload_workflow_configs(file: UploadFile = File(...)):
    
    return await UploadService().upload_workflow_configs(file)


@router.post(
    "/coordinators",
    response_model=UploadResponse,
    summary="Upload Coordinators",
)
async def upload_coordinators(file: UploadFile = File(...)):
   
    return await UploadService().upload_coordinators(file)
