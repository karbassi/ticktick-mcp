from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo


@dataclass
class ParsedDateTime:
    year: int
    month: int
    day: int
    hour: int | None = None
    minute: int | None = None

    @property
    def is_all_day(self) -> bool:
        return self.hour is None

    def to_api_string(self, tz_name: str | None = None) -> str:
        """Format as TickTick API datetime string with UTC offset.

        Example: "2026-02-16T14:30:00.000-0600"
        """
        hour = self.hour if self.hour is not None else 0
        minute = self.minute if self.minute is not None else 0

        tz = ZoneInfo(tz_name) if tz_name else datetime.now(UTC).astimezone().tzinfo  # type: ignore[assignment]

        dt = datetime(self.year, self.month, self.day, hour, minute, tzinfo=tz)
        offset = dt.utcoffset()
        if offset is None:
            offset_str = "+0000"
        else:
            total_secs = int(offset.total_seconds())
            sign = "+" if total_secs >= 0 else "-"
            total_secs = abs(total_secs)
            offset_str = f"{sign}{total_secs // 3600:02d}{(total_secs % 3600) // 60:02d}"

        dt_str = f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
        return f"{dt_str}T{hour:02d}:{minute:02d}:00.000{offset_str}"

    def add_duration(self, duration: Duration) -> ParsedDateTime:
        if self.is_all_day:
            raise ValueError("Cannot add duration to an all-day date (no time component)")

        assert self.hour is not None and self.minute is not None
        total_minutes = (self.hour * 60 + self.minute) + (duration.hours * 60 + duration.minutes)
        extra_days = total_minutes // (24 * 60)
        remaining = total_minutes % (24 * 60)
        new_hour = remaining // 60
        new_minute = remaining % 60

        d = date(self.year, self.month, self.day) + timedelta(days=extra_days)
        return ParsedDateTime(d.year, d.month, d.day, new_hour, new_minute)


@dataclass
class Duration:
    hours: int
    minutes: int


def parse_datetime(input_str: str) -> ParsedDateTime:
    """Parse a user-provided datetime string.

    Accepts: "today", "tomorrow", "YYYY-MM-DD", "YYYY-MM-DDTHH:MM"
    """
    s = input_str.strip().lower()

    if s == "today":
        today = date.today()
        return ParsedDateTime(today.year, today.month, today.day)

    if s == "tomorrow":
        tomorrow = date.today() + timedelta(days=1)
        return ParsedDateTime(tomorrow.year, tomorrow.month, tomorrow.day)

    if "t" in s:
        date_part, time_part = s.split("t", 1)
        year, month, day = _parse_date_part(date_part, input_str)
        hour, minute = _parse_time_part(time_part, input_str)
        return ParsedDateTime(year, month, day, hour, minute)

    year, month, day = _parse_date_part(s, input_str)
    return ParsedDateTime(year, month, day)


def _parse_date_part(s: str, original: str) -> tuple[int, int, int]:
    parts = s.split("-")
    if len(parts) != 3:
        raise ValueError(f"Invalid date '{original}': expected YYYY-MM-DD, 'today', or 'tomorrow'")
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError as e:
        raise ValueError(f"Invalid date '{original}': non-numeric components") from e
    if not 1 <= month <= 12:
        raise ValueError(f"Month out of range in '{original}'")
    if not 1 <= day <= 31:
        raise ValueError(f"Day out of range in '{original}'")
    return year, month, day


def _parse_time_part(s: str, original: str) -> tuple[int, int]:
    parts = s.split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time in '{original}': expected HH:MM")
    try:
        hour, minute = int(parts[0]), int(parts[1])
    except ValueError as e:
        raise ValueError(f"Invalid time in '{original}': non-numeric components") from e
    if hour > 23:
        raise ValueError(f"Hour out of range in '{original}'")
    if minute > 59:
        raise ValueError(f"Minute out of range in '{original}'")
    return hour, minute


def parse_duration(input_str: str) -> Duration:
    """Parse a duration string like "1h", "30m", "1h30m"."""
    s = input_str.strip().lower()
    if not s:
        raise ValueError("Invalid duration: empty string")
    if "-" in s:
        raise ValueError(f"Invalid duration '{input_str}': negative durations are not allowed")

    hours: int | None = None
    minutes: int | None = None
    num_buf = ""

    for ch in s:
        if ch.isdigit():
            num_buf += ch
        elif ch == "h":
            if not num_buf:
                raise ValueError(f"Invalid duration '{input_str}': expected a number before 'h'")
            if hours is not None:
                raise ValueError(f"Invalid duration '{input_str}': duplicate 'h' component")
            hours = int(num_buf)
            num_buf = ""
        elif ch == "m":
            if not num_buf:
                raise ValueError(f"Invalid duration '{input_str}': expected a number before 'm'")
            if minutes is not None:
                raise ValueError(f"Invalid duration '{input_str}': duplicate 'm' component")
            minutes = int(num_buf)
            num_buf = ""
        else:
            raise ValueError(f"Invalid duration '{input_str}': unexpected character '{ch}'")

    if num_buf:
        raise ValueError(f"Invalid duration '{input_str}': missing unit (h or m)")

    if hours is None and minutes is None:
        raise ValueError(f"Invalid duration '{input_str}'")

    h = hours or 0
    m = minutes or 0
    if h == 0 and m == 0:
        raise ValueError(f"Invalid duration '{input_str}': duration must be greater than zero")

    return Duration(hours=h, minutes=m)


def date_to_stamp(input_str: str) -> int:
    """Convert a date string to YYYYMMDD integer stamp.

    Accepts: "YYYY-MM-DD", "today", "yesterday"
    """
    s = input_str.strip().lower()

    if s == "today":
        today = date.today()
        return today.year * 10000 + today.month * 100 + today.day

    if s == "yesterday":
        yesterday = date.today() - timedelta(days=1)
        return yesterday.year * 10000 + yesterday.month * 100 + yesterday.day

    parts = s.split("-")
    if len(parts) != 3:
        raise ValueError(
            f"Invalid date '{input_str}': expected YYYY-MM-DD, 'today', or 'yesterday'"
        )
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError as e:
        raise ValueError(f"Invalid date '{input_str}': non-numeric components") from e
    if not 1 <= month <= 12:
        raise ValueError(f"Month out of range in '{input_str}'")
    if not 1 <= day <= 31:
        raise ValueError(f"Day out of range in '{input_str}'")

    return year * 10000 + month * 100 + day


_EPOCH_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def date_to_epoch_ms(input_str: str) -> int:
    """Convert a date string to epoch milliseconds (midnight UTC).

    Accepts: "YYYY-MM-DD", "today", "yesterday"
    """
    s = input_str.strip().lower()

    if s == "today":
        d = date.today()
    elif s == "yesterday":
        d = date.today() - timedelta(days=1)
    else:
        m = _EPOCH_DATE_RE.match(s)
        if not m:
            raise ValueError(f"Invalid date '{input_str}'")
        d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    dt = datetime(d.year, d.month, d.day, tzinfo=UTC)
    return int(dt.timestamp() * 1000)
