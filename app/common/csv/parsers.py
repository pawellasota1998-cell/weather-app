from datetime import date, datetime

from common.csv.exceptions import CsvReadError


def parse_csv_date(
    raw_value: str,
    *,
    line_number: int,
    column_name: str,
    date_format: str = "%Y-%m-%d",
    expected_format_description: str = "YYYY-MM-DD",
) -> date:
    try:
        return datetime.strptime(
            raw_value,
            date_format,
        ).date()
    except ValueError as exc:
        raise CsvReadError(
            f"Wiersz {line_number}: nieprawidłowa data "
            f"'{raw_value}' w kolumnie '{column_name}'. "
            f"Oczekiwany format: "
            f"{expected_format_description}."
        ) from exc