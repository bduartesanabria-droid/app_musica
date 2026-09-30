from datetime import datetime, timezone

from app.utils.timezone import SPANISH_WEEKDAYS, bogota_date, local_period_starts


def test_bogota_date_handles_utc_day_boundary():
    utc_time = datetime(2026, 6, 1, 2, 0, tzinfo=timezone.utc)

    assert bogota_date(utc_time).isoformat() == "2026-05-31"


def test_period_starts_use_bogota_calendar():
    now = datetime(2026, 6, 3, 3, 0, tzinfo=timezone.utc)
    week_start, month_start = local_period_starts(now)

    assert week_start == datetime(2026, 6, 1, 5, 0)
    assert month_start == datetime(2026, 6, 1, 5, 0)
    assert SPANISH_WEEKDAYS[bogota_date(now).weekday()] == "martes"
