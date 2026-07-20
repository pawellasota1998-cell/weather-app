from common.csv.exceptions import CsvReadError


def is_empty_csv_row(row: dict[str | None, str | list[str | None]]) -> bool:
    # Funkcja sprawdza czy mamy jakiś cały pusty wiersz
    values = [
        value
        for key, value in row.items()
        if key is not None  # Pomijamy klucze z none, none może powstać jak plik zawiera więcej woierszy niż nagłówków
    ]

    return all(
        value is None or (isinstance(value, str) and not value.strip()) for value in values  # Sprawdzamy pusty wiersz
    )


def get_required_csv_value(row: dict[str | None, str | list[str] | None], column_name: str, line_number: int) -> str:
    value = row.get(column_name)

    if value is None or not isinstance(value, str) or not value.strip():
        raise CsvReadError(f"Wiersz {line_number}: kolumna {column_name} nie może być pusta")
    return value.strip()
