from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.enums.alert_type import AlertType


class AlertRuleModel(BaseModel):

    model_config = ConfigDict(extra="forbid")

    ruleId: str

    alertType: AlertType

    description: str

    appliesToZone: str

    condition: str

    threshold: str

    baseSeverity: int = Field(
        ...,
        ge=0,
        le=100
    )

    enabled: bool = True

    createdAt: datetime | None = None