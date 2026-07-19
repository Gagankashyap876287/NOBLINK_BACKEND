from pandas import DataFrame

from app.core.exceptions import BadRequestError


def normalize_csv_columns(dataframe: DataFrame) -> DataFrame:
    dataframe = dataframe.copy()
    dataframe.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in dataframe.columns
    ]
    return dataframe


def rename_csv_columns(
    dataframe: DataFrame,
    column_mapping: dict[str, str],
) -> DataFrame:
    dataframe = dataframe.copy()
    dataframe.rename(columns=column_mapping, inplace=True)
    return dataframe


def format_validation_error(error: dict) -> str:
    location = ".".join(str(part) for part in error.get("loc", ()))
    message = error.get("msg", "Invalid value")

    if location:
        return f"{message} ({location})"

    return message


def require_columns(dataframe: DataFrame, required: list[str]) -> None:
    missing = [column for column in required if column not in dataframe.columns]

    if missing:
        raise BadRequestError(f"Missing columns: {missing}")
