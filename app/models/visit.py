from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VisitModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sensorId: str = Field(..., min_length=1)
    resident: str = Field(..., min_length=1)
    room: str
    zone: str
    facility: str
    region: str
    workflowName: str
    entryTime: datetime
    lastPingTime: datetime
    exitTime: datetime | None = None
    durationMinutes: float = Field(..., ge=0)
    pingCount: int = Field(..., ge=1)
    autoExited: bool = True
    triggerEvents: list[str] = Field(default_factory=list)
    createdAt: datetime | None = None
