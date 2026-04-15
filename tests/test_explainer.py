"""Tests for cronwarden.explainer."""

import pytest
from cronwarden.explainer import explain_schedule


@pytest.mark.parametrize("schedule,expected_fragment", [
    ("@yearly",   "January"),
    ("@annually", "January"),
    ("@monthly",  "midnight on the 1st"),
    ("@weekly",   "Sunday"),
    ("@daily",    "midnight"),
    ("@midnight", "midnight"),
    ("@hourly",   "hour"),
    ("@reboot",   "startup"),
])
def test_special_schedules(schedule, expected_fragment):
    result = explain_schedule(schedule)
    assert expected_fragment in result


def test_every_minute():
    result = explain_schedule("* * * * *")
    assert "every minute" in result
    assert "every hour" in result


def test_specific_minute_and_hour():
    result = explain_schedule("30 9 * * *")
    assert "minute 30" in result
    assert "hour 9" in result


def test_step_value():
    result = explain_schedule("*/15 * * * *")
    assert "every 15 minutes" in result


def test_day_of_week():
    result = explain_schedule("0 8 * * 1")
    assert "Monday" in result


def test_month_name():
    result = explain_schedule("0 0 1 6 *")
    assert "June" in result


def test_comma_separated_days():
    result = explain_schedule("0 9 * * 1,3,5")
    assert "Monday" in result
    assert "Wednesday" in result
    assert "Friday" in result


def test_range_hours():
    result = explain_schedule("0 9-17 * * *")
    assert "from 9 to 17" in result


def test_invalid_schedule_returns_message():
    result = explain_schedule("not a cron")
    assert "Invalid" in result or "unrecognised" in result


def test_result_is_string():
    assert isinstance(explain_schedule("0 0 * * *"), str)
