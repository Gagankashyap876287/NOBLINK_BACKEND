import csv
import io

from fastapi.responses import StreamingResponse

from app.core.exceptions import BadRequestError, NotFoundError
from app.database.collections import Collections
from app.utils.serialize import serialize_documents


CONFIG_TYPES = {
    "sensor-registry": {
        "label": "sensor registry",
        "filename": "Sensor_Registry.csv",
        "collection": Collections.sensor_registry,
    },
    "alert-rules": {
        "label": "alert rules",
        "filename": "Alert_Rules.csv",
        "collection": Collections.alert_rules,
    },
    "workflow-configs": {
        "label": "workflow configs",
        "filename": "Workflow_Configuration.csv",
        "collection": Collections.workflow_configs,
    },
    "coordinators": {
        "label": "coordinators",
        "filename": "Coordinator_Context.csv",
        "collection": Collections.coordinators,
    },
}


class ConfigExportService:

    async def status(self) -> dict:
        configs = []

        for key, meta in CONFIG_TYPES.items():
            collection = meta["collection"]()
            count = await collection.count_documents({})
            latest = None

            if count:
                doc = await collection.find_one(
                    sort=[("createdAt", -1)],
                    projection={"createdAt": 1},
                )
                latest = doc.get("createdAt") if doc else None

            configs.append(
                {
                    "key": key,
                    "label": meta["label"],
                    "filename": meta["filename"],
                    "recordCount": count,
                    "uploaded": count > 0,
                    "uploadedAt": latest,
                }
            )

        return {
            "success": True,
            "configs": serialize_documents(configs),
            "readyForPings": all(item["uploaded"] for item in configs),
        }

    async def export_csv(self, config_key: str) -> StreamingResponse:
        meta = CONFIG_TYPES.get(config_key)

        if meta is None:
            raise BadRequestError(
                f"Unknown config type '{config_key}'. "
                f"Expected one of: {', '.join(CONFIG_TYPES)}."
            )

        documents = await meta["collection"]().find().to_list(None)

        if not documents:
            raise NotFoundError(
                f"No {meta['label']} uploaded yet. Upload a CSV first."
            )

        rows = self._to_csv_rows(config_key, documents)

        if not rows:
            raise NotFoundError(
                f"No {meta['label']} rows available to export."
            )

        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

        buffer.seek(0)
        payload = buffer.getvalue().encode("utf-8")
        return StreamingResponse(
            iter([payload]),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{meta["filename"]}"'
            },
        )

    def _to_csv_rows(self, config_key: str, documents: list[dict]) -> list[dict]:
        if config_key == "sensor-registry":
            return [
                {
                    "Sensor_ID": doc.get("sensorId", ""),
                    "Resident": (doc.get("resident") or {}).get("name", ""),
                    "Room": doc.get("room", ""),
                    "Zone": doc.get("zone", ""),
                    "Facility": doc.get("facility", ""),
                    "Region": doc.get("region", ""),
                    "Workflow": doc.get("workflowName", ""),
                }
                for doc in documents
            ]

        if config_key == "alert-rules":
            return [
                {
                    "Rule_ID": doc.get("ruleId", ""),
                    "Alert_Type": self._enum_value(doc.get("alertType")),
                    "Description": doc.get("description", ""),
                    "Applies_To_Zone": doc.get("appliesToZone", ""),
                    "Condition": doc.get("condition", ""),
                    "Threshold": doc.get("threshold", ""),
                    "Base_Severity": doc.get("baseSeverity", ""),
                }
                for doc in documents
            ]

        if config_key == "workflow-configs":
            rows = []
            for doc in documents:
                for step in doc.get("steps") or []:
                    rows.append(
                        {
                            "Workflow_Name": doc.get("workflowName", ""),
                            "Step_Name": step.get("stepName", ""),
                            "Step_Order": step.get("order", ""),
                            "Max_Response_Hours": step.get("maxResponseHours", ""),
                            "Requires_Note": "Yes" if step.get("requiresNote") else "No",
                            "Auto_Escalate": "Yes" if step.get("autoEscalate") else "No",
                        }
                    )
            return rows

        if config_key == "coordinators":
            return [
                {
                    "Coordinator_ID": doc.get("coordinatorId", ""),
                    "Name": doc.get("name", ""),
                    "Role": self._enum_value(doc.get("role")),
                    "Region": doc.get("region", ""),
                    "Target_Open_Cases": doc.get("targetOpenCases", ""),
                    "Baseline_Resolution_Hours": doc.get(
                        "baselineResolutionHours", ""
                    ),
                }
                for doc in documents
            ]

        raise BadRequestError(f"Unsupported config type '{config_key}'.")

    @staticmethod
    def _enum_value(value) -> str:
        if value is None:
            return ""
        if hasattr(value, "value"):
            return str(value.value)
        return str(value)
