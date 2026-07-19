from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.services.upload_service import SensorPingUploadService


@pytest.mark.asyncio
async def test_duplicate_sensor_ping_upload_reports_already_stored():
    service = SensorPingUploadService.__new__(SensorPingUploadService)
    service.ping_repository = AsyncMock()
    service.ping_repository.all_exist = AsyncMock(return_value=True)
    service.registry_repository = AsyncMock()
    service.visit_service = AsyncMock()
    service.alert_service = AsyncMock()

    service._assert_config_uploaded = AsyncMock()
    service._parse_ping_csv = AsyncMock(
        return_value=[
            {
                "sensorId": "S1",
                "timestamp": datetime(2026, 4, 19, 8, 0),
                "eventType": "presence",
                "batteryPercentage": 90,
            }
        ]
    )
    service._assert_sensors_registered = AsyncMock()

    result = await service.upload(file=AsyncMock())

    assert result["alreadyStored"] is True
    assert "already stored" in result["message"].lower()
    assert result["rawPingsInserted"] == 0
    service.visit_service.generate_and_save_visits.assert_not_called()
    service.alert_service.generate_and_save_alerts.assert_not_called()
    service.ping_repository.bulk_upsert.assert_not_called()
