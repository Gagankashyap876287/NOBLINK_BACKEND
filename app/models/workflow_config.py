from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkflowStep(BaseModel):

    order: int

    stepName: str

    maxResponseHours: int

    requiresNote: bool

    autoEscalate: bool


class WorkflowConfigurationModel(BaseModel):

    model_config = ConfigDict(extra="forbid")

    workflowName: str

    steps: list[WorkflowStep]

    createdAt: datetime | None = None