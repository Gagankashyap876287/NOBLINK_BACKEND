from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Resident(BaseModel):
    name: str = Field(..., min_length=1)


class SensorRegistryModel(BaseModel):

    model_config = ConfigDict(extra="forbid")

    sensorId: str = Field(..., min_length=1)

    resident: Resident

    room: str

    zone: str

    facility: str

    region: str

    workflowName: str

    isActive: bool = True

    createdAt: datetime | None = None

    updatedAt: datetime | None = None