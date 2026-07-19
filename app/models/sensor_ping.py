from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.enums.event_type import EventType


class SensorPingModel(BaseModel):

    model_config = ConfigDict(extra="forbid")

    sensorId: str = Field(..., min_length=1)

    timestamp: datetime

    eventType: EventType

    batteryPercentage: int = Field(
        ...,
        ge=0,
        le=100
    )

    createdAt: datetime | None = None