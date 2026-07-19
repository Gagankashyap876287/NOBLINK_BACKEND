
from fastapi import UploadFile
import pandas as pd
from pydantic import ValidationError

from app.core.constants import (
    ALERT_RULES_COLUMN_MAPPING,
    COORDINATOR_COLUMN_MAPPING,
    MAX_CONFIG_UPLOAD_BYTES,
    MAX_CONFIG_UPLOAD_ROWS,
    MAX_SENSOR_PING_UPLOAD_BYTES,
    MAX_SENSOR_PING_UPLOAD_ROWS,
    REQUIRED_CONFIG_COLLECTIONS,
    SENSOR_PING_COLUMN_MAPPING,
    SENSOR_PING_REQUIRED_COLUMNS,
    SENSOR_REGISTRY_COLUMN_MAPPING,
    UPLOAD_ORDER_MESSAGE,
    WORKFLOW_CONFIG_COLUMN_MAPPING,
)
from app.core.exceptions import BadRequestError
from app.database.collections import Collections
from app.models.alert_rule import AlertRuleModel
from app.models.coordinator import CoordinatorModel
from app.models.sensor_ping import SensorPingModel
from app.models.sensor_registry import SensorRegistryModel
from app.models.workflow_config import WorkflowConfigurationModel
from app.repositories.sensor_ping_repository import SensorPingRepository
from app.repositories.sensor_registry_repository import SensorRegistryRepository
from app.repositories.upload_repository import UploadRepository
from app.services.alert_service import AlertService
from app.services.visit_service import VisitService
from app.transformers.workflow_transformer import WorkflowTransformer
from app.utils.csv_normalizer import (
    format_validation_error,
    normalize_csv_columns,
    rename_csv_columns,
    require_columns,
)
from app.utils.csv_reader import CsvReader
from app.utils.csv_validator import CsvValidator
from app.utils.time import utc_now


class UploadService:
    

    def __init__(self):
        self.repository = UploadRepository()


    async def upload_sensor_registry(self, file: UploadFile) -> dict:
        rows = await self._read_csv(file, SENSOR_REGISTRY_COLUMN_MAPPING)

        documents = []
        for index, row in enumerate(rows, start=2):
            # CSV has "R. Naidoo" — model expects {"name": "R. Naidoo"}
            if row.get("resident") is not None and not isinstance(
                row["resident"], dict
            ):
                row["resident"] = {"name": row["resident"]}

            row["createdAt"] = utc_now()
            documents.append(
                self._validate_row(index, SensorRegistryModel, row)
            )

        inserted = await self.repository.replace(
            Collections.sensor_registry(),
            documents,
        )

        return self._ok("sensor_registry", len(rows), inserted)

    async def upload_alert_rules(self, file: UploadFile) -> dict:
        rows = await self._read_csv(file, ALERT_RULES_COLUMN_MAPPING)

        documents = []
        for index, row in enumerate(rows, start=2):
            # pandas may leave numbers as int/float
            if row.get("threshold") is not None:
                row["threshold"] = str(row["threshold"])
            if row.get("baseSeverity") is not None:
                row["baseSeverity"] = self._coerce_int(
                    index, "baseSeverity", row["baseSeverity"]
                )

            row["createdAt"] = utc_now()
            documents.append(self._validate_row(index, AlertRuleModel, row))

        inserted = await self.repository.replace(
            Collections.alert_rules(),
            documents,
        )

        return self._ok("alert_rules", len(rows), inserted)

    async def upload_workflow_configs(self, file: UploadFile) -> dict:
        rows = await self._read_csv(file, WORKFLOW_CONFIG_COLUMN_MAPPING)

        try:
            grouped = WorkflowTransformer.transform(rows)
        except Exception as exc:
            raise BadRequestError(
                f"Invalid workflow configuration rows: {exc}"
            ) from exc

        documents = []
        for index, row in enumerate(grouped, start=1):
            row["createdAt"] = utc_now()
            documents.append(
                self._validate_row(index, WorkflowConfigurationModel, row)
            )

        inserted = await self.repository.replace(
            Collections.workflow_configs(),
            documents,
        )

        return self._ok("workflow_configs", len(grouped), inserted)

    async def upload_coordinators(self, file: UploadFile) -> dict:
        rows = await self._read_csv(file, COORDINATOR_COLUMN_MAPPING)

        documents = []
        for index, row in enumerate(rows, start=2):
            if row.get("targetOpenCases") is not None:
                row["targetOpenCases"] = self._coerce_int(
                    index, "targetOpenCases", row["targetOpenCases"]
                )
            if row.get("baselineResolutionHours") is not None:
                row["baselineResolutionHours"] = self._coerce_int(
                    index,
                    "baselineResolutionHours",
                    row["baselineResolutionHours"],
                )

            row["createdAt"] = utc_now()
            documents.append(self._validate_row(index, CoordinatorModel, row))

        inserted = await self.repository.replace(
            Collections.coordinators(),
            documents,
        )

        return self._ok("coordinators", len(rows), inserted)

   
    async def _read_csv(
        self,
        file: UploadFile,
        column_mapping: dict[str, str],
    ) -> list[dict]:
        CsvValidator.validate_file(file)
        CsvValidator.validate_size(
            file,
            MAX_CONFIG_UPLOAD_BYTES,
            label="Config CSV",
        )

        try:
            dataframe = await CsvReader.read(file)
        except BadRequestError:
            raise
        except Exception as exc:
            raise BadRequestError(f"Unable to read CSV file: {exc}") from exc

        CsvValidator.validate_empty(dataframe)
        CsvValidator.validate_row_count(
            dataframe,
            MAX_CONFIG_UPLOAD_ROWS,
            label="Config CSV",
        )
        dataframe = normalize_csv_columns(dataframe)
        require_columns(dataframe, list(column_mapping.keys()))
        dataframe = rename_csv_columns(dataframe, column_mapping)
        return dataframe.to_dict(orient="records")

    @staticmethod
    def _validate_row(index: int, model_cls, row: dict) -> dict:
        try:
            return model_cls(**row).model_dump()
        except ValidationError as exc:
            raise BadRequestError(
                f"Row {index}: {format_validation_error(exc.errors()[0])}",
                details=exc.errors(),
            ) from exc
        except (TypeError, ValueError) as exc:
            raise BadRequestError(f"Row {index}: {exc}") from exc

    @staticmethod
    def _coerce_int(index: int, field: str, value) -> int:
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise BadRequestError(
                f"Row {index}: {field} must be an integer (got {value!r})."
            ) from exc

    @staticmethod
    def _ok(label: str, total: int, inserted: int) -> dict:
        return {
            "success": True,
            "message": f"{label} uploaded successfully.",
            "totalRecords": total,
            "insertedRecords": inserted,
        }


class SensorPingUploadService:

    def __init__(self):
        self.ping_repository = SensorPingRepository()
        self.registry_repository = SensorRegistryRepository()
        self.visit_service = VisitService()
        self.alert_service = AlertService()

    async def upload(self, file: UploadFile) -> dict:
        await self._assert_config_uploaded()
        documents = await self._parse_ping_csv(file)
        await self._assert_sensors_registered(documents)

        if await self.ping_repository.all_exist(documents):
            return {
                "success": True,
                "alreadyStored": True,
                "message": (
                    "This sensor ping data is already stored. "
                    "You uploaded the same pings again — no changes were made. "
                    "To rebuild visits/alerts, clear the database first "
                    "(python -m scripts.clear_db) or upload a different ping file."
                ),
                "rawPingsInserted": 0,
                "visitsGenerated": 0,
                "alertsGenerated": 0,
            }

        # Rebuild derived state so re-uploads with new pings stay idempotent
        await Collections.alert_event_logs().delete_many({})
        await Collections.alerts().delete_many({})
        await Collections.visits().delete_many({})

        raw_inserted = await self.ping_repository.bulk_upsert(documents)
        visits = await self.visit_service.generate_and_save_visits(documents)
        alerts = await self.alert_service.generate_and_save_alerts(
            visits,
            sensor_pings=documents,
        )

        return {
            "success": True,
            "alreadyStored": False,
            "message": "Sensor pings processed successfully.",
            "rawPingsInserted": raw_inserted,
            "visitsGenerated": len(visits),
            "alertsGenerated": len(alerts),
        }

    async def _assert_config_uploaded(self) -> None:
        accessors = {
            "sensor_registry": Collections.sensor_registry,
            "alert_rules": Collections.alert_rules,
            "workflow_configs": Collections.workflow_configs,
            "coordinators": Collections.coordinators,
        }

        missing: list[str] = []

        for collection_name, label in REQUIRED_CONFIG_COLLECTIONS:
            count = await accessors[collection_name]().count_documents({})
            if count == 0:
                missing.append(label)

        if missing:
            raise BadRequestError(
                "Upload config files first before sensor pings. "
                f"Missing: {', '.join(missing)}. "
                f"Required order: {UPLOAD_ORDER_MESSAGE}."
            )

    async def _parse_ping_csv(self, file: UploadFile) -> list[dict]:
        CsvValidator.validate_file(file)
        CsvValidator.validate_size(
            file,
            MAX_SENSOR_PING_UPLOAD_BYTES,
            label="Sensor pings CSV",
        )

        try:
            dataframe = await CsvReader.read(file)
        except BadRequestError:
            raise
        except Exception as exc:
            raise BadRequestError(f"Unable to read CSV file: {exc}") from exc

        CsvValidator.validate_empty(dataframe)
        CsvValidator.validate_row_count(
            dataframe,
            MAX_SENSOR_PING_UPLOAD_ROWS,
            label="Sensor pings CSV",
        )
        dataframe = normalize_csv_columns(dataframe)
        require_columns(dataframe, SENSOR_PING_REQUIRED_COLUMNS)
        dataframe = rename_csv_columns(dataframe, SENSOR_PING_COLUMN_MAPPING)

        try:
            dataframe["timestamp"] = pd.to_datetime(
                dataframe["timestamp"],
                utc=False,
            )
        except Exception as exc:
            raise BadRequestError("Invalid timestamp values in CSV.") from exc

        documents = []
        for index, row in enumerate(dataframe.to_dict(orient="records"), start=2):
            row["createdAt"] = utc_now()

            timestamp = row.get("timestamp")
            if pd.isna(timestamp):
                raise BadRequestError(
                    f"Row {index}: timestamp is missing or invalid."
                )
            if hasattr(timestamp, "to_pydatetime"):
                row["timestamp"] = timestamp.to_pydatetime()

            battery = row.get("batteryPercentage")
            if battery is not None and not pd.isna(battery):
                try:
                    row["batteryPercentage"] = int(battery)
                except (TypeError, ValueError) as exc:
                    raise BadRequestError(
                        f"Row {index}: batteryPercentage must be an integer "
                        f"(got {battery!r})."
                    ) from exc
            else:
                row["batteryPercentage"] = None

            try:
                documents.append(SensorPingModel(**row).model_dump())
            except ValidationError as exc:
                raise BadRequestError(
                    f"Row {index}: {format_validation_error(exc.errors()[0])}",
                    details=exc.errors(),
                ) from exc

        return documents

    async def _assert_sensors_registered(self, documents: list[dict]) -> None:
        unknown: set[str] = set()

        for document in documents:
            registry = await self.registry_repository.get_by_sensor(
                document["sensorId"]
            )
            if registry is None:
                unknown.add(document["sensorId"])

        if unknown:
            raise BadRequestError(
                f"Unknown sensor IDs (not in registry): {sorted(unknown)}"
            )
