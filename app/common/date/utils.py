from datetime import date


def get_next_month_first_date (month_start: date) -> date:
    if month_start.month == 12:
        return date(
            year=month_start.year + 1,
            month=1,
            day=1,
        )

    return date(
        year=month_start.year,
        month=month_start.month + 1,
        day=1,
    )