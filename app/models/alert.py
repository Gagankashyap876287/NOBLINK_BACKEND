from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.enums.alert_type import AlertType


class AlertWorkflow(BaseModel):
    workflowName: str
    currentStep: int
    currentStepName: str
    stepStartedAt: datetime


class AlertLocation(BaseModel):
    region: str
    facility: str
    room: str
    zone: str | None = None


class AlertTiming(BaseModel):
    createdAt: datetime
    updatedAt: datetime
    resolvedAt: datetime | None = None


class AlertModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    visitId: Any | None = None
    sensorId: str = Field(..., min_length=1)
    resident: str
    coordinatorId: Any | None = None
    ruleId: str | None = None
    alertType: AlertType
    severity: int = Field(..., ge=0, le=100)
    riskScore: int = Field(..., ge=0, le=100)
    status: str = "OPEN"
    workflow: AlertWorkflow
    location: AlertLocation
    timing: AlertTiming
