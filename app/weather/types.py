from dataclasses import dataclass
from datetime import date
from decimal import Decimal


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


@dataclass(frozen=True, slots=True)
class MonthlyPrecipitationStatistics:
    year: int
    month: int
    measurement_count: int
    average_snow: Decimal
    average_rain: Decimal
    average_total: Decimal
