from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import IO

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Field

from common.csv.exceptions import CsvReadError
from common.csv.parsers import parse_csv_date
from common.csv.readers import read_text_file
from common.csv.rows import get_required_csv_value, is_empty_csv_row
from weather.exceptions import PrecipitationCsvError
from weather.models import PrecipitationMeasurement
from weather.types import ImportResult, PrecipitationCsvRow

EXPECTED_HEADERS = ("date", "snow", "rain")


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

    return ImportResult(
        created=created,
        updated=updated,
        unchanged=unchanged,
    )


def parse_precipitation_csv(file_obj: IO[bytes] | IO[str]) -> list[PrecipitationCsvRow]:
    try:
        text = read_text_file(file_obj)
    except CsvReadError as exc:
        raise PrecipitationCsvError(str(exc)) from exc

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
        if is_empty_csv_row(raw_row):  # pomijamy cały pusty wiersz
            continue

        if None in raw_row:
            raise PrecipitationCsvError(f"Wiersz {line_number} zawiera więcej kolumn niż nagłówków.")

        try:
            measurement_date = parse_csv_date(
                get_required_csv_value(
                    raw_row,
                    "date",
                    line_number,
                ),
                line_number=line_number,
                column_name="date",
            )
            snow = _parse_precipitation_value(
                get_required_csv_value(raw_row, "snow", line_number),
                column_name="snow",
                model_field_name="snow",
                line_number=line_number,
            )
            rain = _parse_precipitation_value(
                get_required_csv_value(raw_row, "rain", line_number),
                column_name="rain",
                model_field_name="rain",
                line_number=line_number,
            )
        except CsvReadError as exc:
            raise PrecipitationCsvError(str(exc)) from exc

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

    if not isinstance(model_field, Field):
        raise PrecipitationCsvError(f"Pole '{model_field_name}' nie jest zwykłym polem modelu.")

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
