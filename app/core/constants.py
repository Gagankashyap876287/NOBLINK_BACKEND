VISIT_INACTIVITY_MINUTES = 15

NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 6

SENSOR_REGISTRY_COLUMN_MAPPING = {
    "sensor_id": "sensorId",
    "resident": "resident",
    "room": "room",
    "zone": "zone",
    "facility": "facility",
    "region": "region",
    "workflow": "workflowName",
}

ALERT_RULES_COLUMN_MAPPING = {
    "rule_id": "ruleId",
    "alert_type": "alertType",
    "description": "description",
    "applies_to_zone": "appliesToZone",
    "condition": "condition",
    "threshold": "threshold",
    "base_severity": "baseSeverity",
}

WORKFLOW_CONFIG_COLUMN_MAPPING = {
    "workflow_name": "workflowName",
    "step_name": "stepName",
    "step_order": "order",
    "max_response_hours": "maxResponseHours",
    "requires_note": "requiresNote",
    "auto_escalate": "autoEscalate",
}

COORDINATOR_COLUMN_MAPPING = {
    "coordinator_id": "coordinatorId",
    "name": "name",
    "role": "role",
    "region": "region",
    "target_open_cases": "targetOpenCases",
    "baseline_resolution_hours": "baselineResolutionHours",
}

SENSOR_PING_COLUMN_MAPPING = {
    "sensor_id": "sensorId",
    "timestamp": "timestamp",
    "event_type": "eventType",
    "battery_pct": "batteryPercentage",
}

SENSOR_PING_REQUIRED_COLUMNS = list(SENSOR_PING_COLUMN_MAPPING.keys())

# Config collections that must exist before sensor-pings upload.
# (collection accessor name, human-readable label)
REQUIRED_CONFIG_COLLECTIONS = (
    ("sensor_registry", "sensor registry"),
    ("alert_rules", "alert rules"),
    ("workflow_configs", "workflow configs"),
    ("coordinators", "coordinators"),
)

UPLOAD_ORDER_MESSAGE = (
    "sensor registry -> alert rules -> workflow configs -> "
    "coordinators -> sensor pings"
)

# Upload size / row caps (demo-friendly; sample pings are ~13KB / ~300 rows).
MAX_CONFIG_UPLOAD_BYTES = 1 * 1024 * 1024  # 1 MB
MAX_CONFIG_UPLOAD_ROWS = 5_000

MAX_SENSOR_PING_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_SENSOR_PING_UPLOAD_ROWS = 50_000

