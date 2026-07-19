from io import BytesIO

import pandas as pd
import pytest
from fastapi import UploadFile

from app.core.constants import (
    MAX_SENSOR_PING_UPLOAD_BYTES,
    MAX_SENSOR_PING_UPLOAD_ROWS,
)
from app.core.exceptions import BadRequestError
from app.utils.csv_normalizer import require_columns
from app.utils.csv_validator import CsvValidator


def test_reject_non_csv_extension():
    file = UploadFile(filename="pings.txt", file=BytesIO(b"a,b\n1,2\n"))

    with pytest.raises(BadRequestError, match="Only CSV files"):
        CsvValidator.validate_file(file)


def test_reject_oversized_sensor_ping_file():
    payload = b"x" * (MAX_SENSOR_PING_UPLOAD_BYTES + 1)
    file = UploadFile(filename="pings.csv", file=BytesIO(payload))

    with pytest.raises(BadRequestError, match="too large"):
        CsvValidator.validate_size(
            file,
            MAX_SENSOR_PING_UPLOAD_BYTES,
            label="Sensor pings CSV",
        )


def test_reject_too_many_sensor_ping_rows():
    dataframe = pd.DataFrame({"a": range(MAX_SENSOR_PING_UPLOAD_ROWS + 1)})

    with pytest.raises(BadRequestError, match="too many rows"):
        CsvValidator.validate_row_count(
            dataframe,
            MAX_SENSOR_PING_UPLOAD_ROWS,
            label="Sensor pings CSV",
        )


def test_reject_missing_required_columns():
    dataframe = pd.DataFrame({"sensor_id": ["S1"], "timestamp": ["2026-01-01"]})

    with pytest.raises(BadRequestError, match="Missing columns"):
        require_columns(
            dataframe,
            ["sensor_id", "timestamp", "event_type", "battery_pct"],
        )
