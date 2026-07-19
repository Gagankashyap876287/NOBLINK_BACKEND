from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import BadRequestError
from app.services.upload_service import SensorPingUploadService


@pytest.mark.asyncio
async def test_sensor_ping_upload_blocked_without_config():
    service = SensorPingUploadService.__new__(SensorPingUploadService)
    empty = AsyncMock(return_value=0)

    with (
        patch(
            "app.services.upload_service.Collections.sensor_registry",
            return_value=AsyncMock(count_documents=empty),
        ),
        patch(
            "app.services.upload_service.Collections.alert_rules",
            return_value=AsyncMock(count_documents=empty),
        ),
        patch(
            "app.services.upload_service.Collections.workflow_configs",
            return_value=AsyncMock(count_documents=empty),
        ),
        patch(
            "app.services.upload_service.Collections.coordinators",
            return_value=AsyncMock(count_documents=empty),
        ),
    ):
        with pytest.raises(BadRequestError, match="Upload config files first"):
            await service._assert_config_uploaded()
