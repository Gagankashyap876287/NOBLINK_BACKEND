from fastapi import UploadFile
import pandas as pd

from app.core.exceptions import BadRequestError


class CsvReader:

    @staticmethod
    async def read(file: UploadFile) -> pd.DataFrame:
        try:
            return pd.read_csv(file.file)
        except Exception as exc:
            raise BadRequestError(f"Unable to parse CSV: {exc}") from exc
