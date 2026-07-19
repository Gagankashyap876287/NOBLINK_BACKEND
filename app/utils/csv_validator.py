from app.core.exceptions import BadRequestError


class CsvValidator:

    @staticmethod
    def validate(file, dataframe) -> None:
        CsvValidator.validate_file(file)
        CsvValidator.validate_empty(dataframe)

    @staticmethod
    def validate_file(file) -> None:
        if file is None:
            raise BadRequestError("File is required.")

        filename = getattr(file, "filename", None) or ""
        if not filename.lower().endswith(".csv"):
            raise BadRequestError("Only CSV files are allowed.")

    @staticmethod
    def validate_size(file, max_bytes: int, label: str = "CSV") -> None:
        size = CsvValidator._file_size_bytes(file)

        if size is None:
            return

        if size > max_bytes:
            max_mb = max_bytes / (1024 * 1024)
            actual_mb = size / (1024 * 1024)
            raise BadRequestError(
                f"{label} file is too large ({actual_mb:.2f} MB). "
                f"Maximum allowed size is {max_mb:.0f} MB."
            )

    @staticmethod
    def validate_empty(dataframe) -> None:
        if dataframe is None or dataframe.empty:
            raise BadRequestError("CSV file is empty.")

    @staticmethod
    def validate_row_count(
        dataframe,
        max_rows: int,
        label: str = "CSV",
    ) -> None:
        row_count = len(dataframe.index)

        if row_count > max_rows:
            raise BadRequestError(
                f"{label} has too many rows ({row_count:,}). "
                f"Maximum allowed is {max_rows:,} rows."
            )

    @staticmethod
    def _file_size_bytes(file) -> int | None:
        size = getattr(file, "size", None)
        if isinstance(size, int) and size >= 0:
            return size

        stream = getattr(file, "file", None)
        if stream is None or not hasattr(stream, "seek") or not hasattr(stream, "tell"):
            return None

        try:
            current = stream.tell()
            stream.seek(0, 2)
            size = stream.tell()
            stream.seek(current)
            return int(size)
        except Exception:
            return None
