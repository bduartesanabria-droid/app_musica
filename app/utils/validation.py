import re

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,50}$")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def valid_username(value):
    return bool(value and USERNAME_PATTERN.fullmatch(value))


def valid_email(value):
    return bool(value and len(value) <= 120 and EMAIL_PATTERN.fullmatch(value))


def valid_password(value):
    if not isinstance(value, str) or len(value) < 8:
        return False
    try:
        return len(value.encode("utf-8")) <= 72
    except UnicodeEncodeError:
        return False
