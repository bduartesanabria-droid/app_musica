from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

BOGOTA = ZoneInfo("America/Bogota")
SPANISH_WEEKDAYS = (
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
)


def utc_now_naive():
    """Return UTC for the app's existing timezone-naive DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def bogota_date(value=None):
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(BOGOTA).date()


def local_day_start_utc(day):
    return datetime.combine(day, time.min, tzinfo=BOGOTA).astimezone(timezone.utc).replace(tzinfo=None)


def local_period_starts(now=None):
    now = now or datetime.now(BOGOTA)
    if now.tzinfo is None:
        now = now.replace(tzinfo=BOGOTA)
    local_day = now.astimezone(BOGOTA).date()
    week_start = local_day_start_utc(local_day - timedelta(days=local_day.weekday()))
    month_start = local_day_start_utc(local_day.replace(day=1))
    return week_start, month_start


def refresh_period_xp(gamification, user_id, now=None):
    from ..extensions import db
    from ..models.session import TrainingSession

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now_utc = now.astimezone(timezone.utc).replace(tzinfo=None)
    week_start, month_start = local_period_starts(now)
    totals = db.session.query(
        TrainingSession.completed_at,
        TrainingSession.xp_earned,
    ).filter(
        TrainingSession.user_id == user_id,
        TrainingSession.is_completed.is_(True),
        TrainingSession.completed_at >= month_start,
        TrainingSession.completed_at <= now_utc,
    ).all()

    monthly_xp = sum(xp or 0 for _, xp in totals)
    weekly_xp = sum(
        xp or 0
        for completed_at, xp in totals
        if completed_at and completed_at >= week_start
    )
    changed = (
        gamification.monthly_xp != monthly_xp
        or gamification.weekly_xp != weekly_xp
    )
    gamification.monthly_xp = monthly_xp
    gamification.weekly_xp = weekly_xp
    return changed
