from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.enums.role import CoordinatorRole


class CoordinatorModel(BaseModel):

    model_config = ConfigDict(extra="forbid")

    coordinatorId: str

    name: str

    role: CoordinatorRole

    region: str

    targetOpenCases: int

    baselineResolutionHours: int

    active: bool = True

    createdAt: datetime | None = None