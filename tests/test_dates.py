from __future__ import annotations

import pytest

from ticktick_mcp.dates import (
    Duration,
    ParsedDateTime,
    date_to_epoch_ms,
    date_to_stamp,
    parse_datetime,
    parse_duration,
)


class TestParseDatetime:
    def test_today(self):
        result = parse_datetime("today")
        assert result.is_all_day
        assert 1 <= result.month <= 12
        assert 1 <= result.day <= 31

    def test_tomorrow(self):
        result = parse_datetime("tomorrow")
        assert result.is_all_day

    def test_date_only(self):
        result = parse_datetime("2026-02-16")
        assert result == ParsedDateTime(2026, 2, 16)
        assert result.is_all_day

    def test_date_and_time(self):
        result = parse_datetime("2026-02-16T14:30")
        assert result == ParsedDateTime(2026, 2, 16, 14, 30)
        assert not result.is_all_day

    def test_case_insensitive(self):
        result = parse_datetime("2026-02-16t09:05")
        assert result.hour == 9
        assert result.minute == 5

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            parse_datetime("not-a-date")
        with pytest.raises(ValueError):
            parse_datetime("")

    def test_month_out_of_range(self):
        with pytest.raises(ValueError):
            parse_datetime("2026-13-01")
        with pytest.raises(ValueError):
            parse_datetime("2026-00-01")

    def test_day_out_of_range(self):
        with pytest.raises(ValueError):
            parse_datetime("2026-01-00")
        with pytest.raises(ValueError):
            parse_datetime("2026-01-32")

    def test_hour_out_of_range(self):
        with pytest.raises(ValueError):
            parse_datetime("2026-01-15T24:00")

    def test_minute_out_of_range(self):
        with pytest.raises(ValueError):
            parse_datetime("2026-01-15T12:60")


class TestParseDuration:
    def test_hours_only(self):
        assert parse_duration("1h") == Duration(1, 0)

    def test_minutes_only(self):
        assert parse_duration("30m") == Duration(0, 30)

    def test_hours_and_minutes(self):
        assert parse_duration("1h30m") == Duration(1, 30)
        assert parse_duration("2h15m") == Duration(2, 15)

    def test_case_insensitive(self):
        assert parse_duration("1H30M") == Duration(1, 30)

    def test_zero(self):
        with pytest.raises(ValueError):
            parse_duration("0h")
        with pytest.raises(ValueError):
            parse_duration("0m")

    def test_empty(self):
        with pytest.raises(ValueError):
            parse_duration("")

    def test_no_unit(self):
        with pytest.raises(ValueError):
            parse_duration("123")

    def test_negative(self):
        with pytest.raises(ValueError):
            parse_duration("-1h")


class TestToApiString:
    def test_date_only_local(self):
        dt = ParsedDateTime(2026, 2, 16)
        s = dt.to_api_string()
        assert s.startswith("2026-02-16T00:00:00.000")
        offset = s[len("2026-02-16T00:00:00.000") :]
        assert len(offset) == 5
        assert offset[0] in "+-"

    def test_datetime_with_timezone(self):
        dt = ParsedDateTime(2026, 7, 15, 14, 0)
        s = dt.to_api_string("UTC")
        assert s == "2026-07-15T14:00:00.000+0000"


class TestAddDuration:
    def test_same_day(self):
        dt = ParsedDateTime(2026, 2, 16, 10, 0)
        result = dt.add_duration(Duration(1, 30))
        assert result == ParsedDateTime(2026, 2, 16, 11, 30)

    def test_day_overflow(self):
        dt = ParsedDateTime(2026, 2, 16, 23, 30)
        result = dt.add_duration(Duration(1, 0))
        assert result == ParsedDateTime(2026, 2, 17, 0, 30)

    def test_month_overflow(self):
        dt = ParsedDateTime(2026, 1, 31, 23, 0)
        result = dt.add_duration(Duration(2, 0))
        assert result == ParsedDateTime(2026, 2, 1, 1, 0)

    def test_errors_on_all_day(self):
        dt = ParsedDateTime(2026, 2, 16)
        with pytest.raises(ValueError):
            dt.add_duration(Duration(1, 0))


class TestDateToStamp:
    def test_specific_date(self):
        assert date_to_stamp("2026-02-18") == 20260218
        assert date_to_stamp("2026-01-01") == 20260101

    def test_today(self):
        stamp = date_to_stamp("today")
        assert stamp >= 20000101
        assert stamp <= 29991231

    def test_yesterday(self):
        today = date_to_stamp("today")
        yesterday = date_to_stamp("yesterday")
        assert yesterday < today or yesterday > today - 200

    def test_invalid(self):
        with pytest.raises(ValueError):
            date_to_stamp("not-a-date")
        with pytest.raises(ValueError):
            date_to_stamp("")


class TestDateToEpochMs:
    def test_specific_date(self):
        ms = date_to_epoch_ms("2026-01-01")
        assert ms == 1767225600000  # 2026-01-01T00:00:00Z

    def test_today(self):
        ms = date_to_epoch_ms("today")
        assert ms > 0
