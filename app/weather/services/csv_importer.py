from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import IO

from django.core.exceptions import ValidationError
from django.db import transaction

from weather.models import PrecipitationMeasurement

EXPECTED_HEADERS = ("date", "snow", "rain")


class PrecipitationCsvError(ValueError):
    """Błąd struktury lub zawartości pliku CSV."""


@dataclass(frozen=True, slots=True)
class PrecipitationCsvRow:
    line_number: int
    measurement_date: date
    snow: Decimal
    rain: Decimal


@dataclass(frozen=True, slots=True)
class ImportResult:
    created: int
    updated: int
    unchanged: int

    @property
    def total(self) -> int:
        return self.created + self.updated + self.unchanged


def import_precipitation_csv(file_obj: IO[bytes] | IO[str]) -> ImportResult:
    """
    Waliduje plik CSV i zapisuje pomiary w bazie danych.

    Istniejący rekord o tej samej dacie:
    - pozostaje bez zmian, jeśli wartości są identyczne,
    - zostaje zaktualizowany, jeśli wartości się różnią.
    """

    rows = parse_precipitation_csv(file_obj)
    created = 0
    updated = 0
    unchanged = 0

    first_date = min(row.measurement_date for row in rows)
    last_date = max(row.measurement_date for row in rows)

    with transaction.atomic():
        existing_measurements = PrecipitationMeasurement.objects.filter(measurement_date__range=(first_date, last_date))

        existing_by_date = {measurement.measurement_date: measurement for measurement in existing_measurements}

        for row in rows:
            measurement = existing_by_date.get(row.measurement_date)

            if measurement is None:  # Jeśli nie mamy pomiaru to go tworzymy
                measurement = PrecipitationMeasurement.objects.create(
                    measurement_date=row.measurement_date, snow=row.snow, rain=row.rain
                )
                existing_by_date[row.measurement_date] = measurement
                created += 1
                continue
            if measurement.snow == row.snow and measurement.rain == row.rain:
                unchanged += 1
                continue

            measurement.snow = row.snow
            measurement.rain = row.rain
            measurement.save(update_fields=["snow", "rain", "updated_at"])
            updated += 1

        return ImportResult(created=created, updated=updated, unchanged=unchanged)

    return ImportResult(created=0, updated=0, unchanged=0)


def parse_precipitation_csv(file_obj: IO[bytes] | IO[str]) -> list[PrecipitationCsvRow]:
    text = _read_file_content(file_obj)

    reader = csv.DictReader(StringIO(text, newline=""), delimiter=";")

    if reader.fieldnames is None:
        raise PrecipitationCsvError("Plik CSV nie zawiera wiersza nagłówkowego.")

    normalized_headers = tuple((header or "").strip().lower() for header in reader.fieldnames)

    if len(normalized_headers) != len(EXPECTED_HEADERS) or set(normalized_headers) != set(EXPECTED_HEADERS):
        expected = ";".join(EXPECTED_HEADERS)
        actual = ";".join(normalized_headers)

        raise PrecipitationCsvError(f"Nieprawidłowe nagłówki csv. Oczekiwano :{expected}, a otrzymano: {actual}")

    reader.fieldnames = list(normalized_headers)  # Pozwala później odwoływać się do kolumn po oczyszczonych nazwach.

    parsed_rows: list[PrecipitationCsvRow] = []
    date_line_number: dict[date, int] = {}

    for line_number, raw_row in enumerate(reader, start=2):
        if _is_empty_row(raw_row):  # pomijamy cały pusty wiersz
            continue

        if None in raw_row:
            raise PrecipitationCsvError(f"Wiersz {line_number} zawiera więcej kolumn niż nagłówków.")

        measurement_date = _parse_date(_get_required_value(raw_row, "date", line_number), line_number)
        snow = _parse_precipitation_value(
            _get_required_value(raw_row, "snow", line_number),
            column_name="snow",
            model_field_name="snow",
            line_number=line_number,
        )
        rain = _parse_precipitation_value(
            _get_required_value(raw_row, "rain", line_number),
            column_name="rain",
            model_field_name="rain",
            line_number=line_number,
        )

        previous_line = date_line_number.get(measurement_date)

        if previous_line is not None:
            raise PrecipitationCsvError(
                f"Wiersz {line_number}: data {measurement_date} "
                f"występuje w pliku ponownie. "
                f"Pierwsze wystąpienie znajduje się w wierszu "
                f"{previous_line}."
            )
        date_line_number[measurement_date] = line_number

        parsed_rows.append(
            PrecipitationCsvRow(line_number=line_number, measurement_date=measurement_date, snow=snow, rain=rain)
        )
        if not parsed_rows:
            raise PrecipitationCsvError("Plik CSV nie zawiera żadnych pomiarów.")
    return parsed_rows

    # REfaktoryzacja


def _read_file_content(file_obj: IO[bytes] | IO[str]) -> str:
    try:
        file_obj.seek(0)
    except (AttributeError, OSError):
        pass

    content = file_obj.read()

    if isinstance(content, str):
        text = content.lstrip("\ufeff")  # Usuwamy z początku tekstu znak \ufeff w celu popranwego odczytania typu
    elif isinstance(content, bytes):
        try:
            text = content.decode("utf-8-sig")  # Zamieniamy dane na tekst,  utf-8-sig usuwa opcjonalny znacznik BOM.
        except UnicodeDecodeError as exc:
            raise PrecipitationCsvError("Plik musi być zapisany w kodowaniu UTF-8") from exc
    else:
        raise PrecipitationCsvError("Nie udało się odczytać zawartości pliku CSV")
    if not text.strip():
        raise PrecipitationCsvError("Plik CSV jest pusty")
    return text


# Refaktoryzacja
def _is_empty_row(row: dict[str | None, str | list[str | None]]) -> bool:
    # Funkcja sprawdza czy mamy jakiś cały pusty wiersz
    values = [
        value
        for key, value in row.items()
        if key is not None  # Pomijamy klucze z none, none może powstać jak plik zawiera więcej woierszy niż nagłówków
    ]

    return all(
        value is None or (isinstance(value, str) and not value.strip()) for value in values  # Sprawdzamy pusty wiersz
    )


# Refaktoryzacja
def _get_required_value(row: dict[str | None, str | list[str] | None], column_name: str, line_number: int) -> str:
    value = row.get(column_name)

    if value is None or not isinstance(value, str) or not value.strip():
        raise PrecipitationCsvError(f"Wiersz {line_number}: kolumna {column_name} nie może być pusta")
    return value.strip()


# Refaktoryzacja
def _parse_date(raw_value: str, line_number: int) -> date:
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise PrecipitationCsvError(
            f"Wiersz {line_number}: nieprawidłowa data '{raw_value}'. Oczekiwany format to YYYY-MM-DD."
        ) from exc


# Refaktoryzacja
def _parse_precipitation_value(raw_value: str, *, column_name: str, model_field_name: str, line_number: int) -> Decimal:
    normalized_value = raw_value.replace(",", ".")

    try:
        value = Decimal(normalized_value)
    except InvalidOperation as exc:
        raise PrecipitationCsvError(
            f"Wiersz {line_number}: wartość '{raw_value}' w kolumnie '{column_name}' nie jest liczbą."
        ) from exc

    if not value.is_finite():
        raise PrecipitationCsvError(
            f"Wiersz {line_number}: wartość w kolumnie '{column_name}' musi być skończoną liczbą."
        )
    if value < 0:
        raise PrecipitationCsvError(f"Wiersz {line_number}: wartość w kolumnie '{column_name}' nie może być ujemna.")

    model_field = PrecipitationMeasurement._meta.get_field(model_field_name)

    try:
        cleaned_value = model_field.clean(value, None)
    except ValidationError as exc:
        errors = " ".join(exc.messages)
        raise PrecipitationCsvError(
            f"Wiersz {line_number}: nieprawidłowa wartość '{raw_value}' w kolumnie '{column_name}'. {errors}"
        ) from exc

    if not isinstance(cleaned_value, Decimal):
        raise PrecipitationCsvError(f"Wiersz {line_number}: nie udało się przetworzyć kolumny '{column_name}'.")
    return cleaned_value
