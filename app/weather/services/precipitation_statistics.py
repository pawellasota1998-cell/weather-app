
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from common.date.utils import get_next_month_first_date
from django.db.models import Avg, Count

from weather.models import PrecipitationMeasurement
from weather.types import MonthlyPrecipitationStatistics
from weather.exceptions import NoPrecipitationMeasurementsError

TWO_DECIMAL_PLACES = Decimal("0.01")


def get_latest_month_statistics() -> MonthlyPrecipitationStatistics:
    latest_measurement_date = (
        PrecipitationMeasurement.objects.order_by("-measurement_date")
        .values_list(
            "measurement_date",
            flat=True,
        )
        .first()
    )

    if latest_measurement_date is None:
        raise NoPrecipitationMeasurementsError("W bazie danych nie ma żadnych pomiarów.")

    month_start = latest_measurement_date.replace(day=1)
    next_month_start = get_next_month_first_date(month_start)

    monthly_measurements = PrecipitationMeasurement.objects.filter(
        measurement_date__gte=month_start,
        measurement_date__lt=next_month_start,
    )

    aggregation = monthly_measurements.aggregate(
        measurement_count=Count("id"),
        average_snow=Avg("snow"),
        average_rain=Avg("rain"),
    )

    measurement_count = aggregation["measurement_count"]
    average_snow = aggregation["average_snow"]
    average_rain = aggregation["average_rain"]

    if measurement_count == 0 or average_snow is None or average_rain is None:
        raise NoPrecipitationMeasurementsError("Nie znaleziono pomiarów dla ostatniego miesiąca.")

    average_total = average_snow + average_rain

    return MonthlyPrecipitationStatistics(
        year=month_start.year,
        month=month_start.month,
        measurement_count=measurement_count,
        average_snow=_round_decimal(average_snow),
        average_rain=_round_decimal(average_rain),
        average_total=_round_decimal(average_total),
    )


def _round_decimal(value: Decimal) -> Decimal:
    return value.quantize(
        TWO_DECIMAL_PLACES,
        rounding=ROUND_HALF_UP,
    )
