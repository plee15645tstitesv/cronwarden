"""Tests for cronwarden.validator module."""

import pytest

from cronwarden.config import CronJob
from cronwarden.validator import (
    ValidationResult,
    validate_job,
    validate_jobs,
    validate_schedule,
)


# ---------------------------------------------------------------------------
# validate_schedule
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("schedule", [
    "* * * * *",
    "0 12 * * *",
    "*/15 * * * *",
    "0 9-17 * * 1-5",
    "30 6 1,15 * *",
    "@reboot",
    "@daily",
    "@hourly",
    "@weekly",
    "@monthly",
    "@yearly",
    "@annually",
    "@midnight",
])
def test_valid_schedules(schedule):
    assert validate_schedule(schedule) is None


@pytest.mark.parametrize("schedule", [
    "* * * *",           # too few fields
    "* * * * * *",       # too many fields
    "60 * * * *",        # minute out of range
    "* 24 * * *",        # hour out of range
    "* * 0 * *",         # day-of-month out of range (< 1)
    "* * * 13 *",        # month out of range
    "* * * * 8",         # day-of-week out of range
    "abc * * * *",       # non-numeric field
    "*/0 * * * *",       # step of zero
    "",                  # empty string
])
def test_invalid_schedules(schedule):
    assert validate_schedule(schedule) is not None


def test_validate_schedule_returns_descriptive_error():
    error = validate_schedule("* * * *")
    assert "5" in error  # mentions expected field count


# ---------------------------------------------------------------------------
# validate_job / validate_jobs
# ---------------------------------------------------------------------------

def _make_job(name: str, schedule: str) -> CronJob:
    return CronJob(name=name, schedule=schedule, command="echo test")


def test_validate_job_returns_validation_result():
    job = _make_job("backup", "0 2 * * *")
    result = validate_job(job)
    assert isinstance(result, ValidationResult)


def test_validate_job_valid():
    job = _make_job("backup", "0 2 * * *")
    result = validate_job(job)
    assert result.valid is True
    assert result.error is None
    assert result.job_name == "backup"


def test_validate_job_invalid():
    job = _make_job("bad_job", "99 * * * *")
    result = validate_job(job)
    assert result.valid is False
    assert result.error is not None


def test_validate_jobs_mixed():
    jobs = [
        _make_job("ok", "@daily"),
        _make_job("broken", "* * * *"),
    ]
    results = validate_jobs(jobs)
    assert len(results) == 2
    assert results[0].valid is True
    assert results[1].valid is False


def test_validation_result_str_ok():
    result = ValidationResult(job_name="myjob", schedule="@daily", valid=True)
    assert str(result).startswith("[OK]")
    assert "myjob" in str(result)


def test_validation_result_str_err():
    result = ValidationResult(
        job_name="badjob", schedule="99 * * * *",
        valid=False, error="invalid minute"
    )
    assert str(result).startswith("[ERR]")
    assert "invalid minute" in str(result)
