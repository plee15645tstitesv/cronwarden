"""Tests for cronwarden.watchdog."""
import pytest
from datetime import datetime, timedelta
from cronwarden.watchdog import check_watchdog, WatchdogResult, OverdueJob
from cronwarden.config import CronJob, Server, Config


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup"):
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config(jobs=None):
    if jobs is None:
        jobs = [_make_job()]
    server = Server(name="prod", host="prod.example.com", jobs=jobs)
    return Config(servers=[server])


def test_check_watchdog_returns_watchdog_result():
    config = _make_config()
    result = check_watchdog(config, {})
    assert isinstance(result, WatchdogResult)


def test_no_overdue_when_recently_seen():
    now = datetime(2024, 6, 1, 3, 0, 0)
    job = _make_job(schedule="0 2 * * *")
    config = _make_config([job])
    # Last seen just after the last scheduled run
    last_seen = datetime(2024, 6, 1, 2, 1, 0)
    result = check_watchdog(config, {("prod", "backup"): last_seen}, reference_time=now)
    assert not result.has_overdue


def test_overdue_when_last_seen_is_old():
    now = datetime(2024, 6, 3, 10, 0, 0)
    job = _make_job(schedule="0 2 * * *")
    config = _make_config([job])
    # Last seen 2 days ago — multiple runs should have happened
    last_seen = datetime(2024, 6, 1, 2, 1, 0)
    result = check_watchdog(config, {("prod", "backup"): last_seen}, reference_time=now)
    assert result.has_overdue
    assert result.total >= 1


def test_never_seen_job_flagged_if_should_have_run():
    # Job runs every minute; reference time is now, so it should have run in last 24h
    now = datetime(2024, 6, 1, 12, 0, 0)
    job = _make_job(schedule="* * * * *")
    config = _make_config([job])
    result = check_watchdog(config, {}, reference_time=now)
    assert result.has_overdue


def test_overdue_job_summary_contains_server_and_name():
    now = datetime(2024, 6, 3, 10, 0, 0)
    job = _make_job(schedule="0 2 * * *")
    config = _make_config([job])
    last_seen = datetime(2024, 6, 1, 2, 1, 0)
    result = check_watchdog(config, {("prod", "backup"): last_seen}, reference_time=now)
    assert result.has_overdue
    s = result.overdue[0].summary()
    assert "prod" in s
    assert "backup" in s


def test_watchdog_result_str_no_overdue():
    result = WatchdogResult(overdue=[])
    assert "on schedule" in str(result)


def test_watchdog_result_str_with_overdue():
    now = datetime(2024, 6, 2, 10, 0, 0)
    job = _make_job()
    overdue = OverdueJob(server="prod", job=job, expected_by=now, last_seen=None)
    result = WatchdogResult(overdue=[overdue])
    assert "1 overdue" in str(result)


def test_invalid_schedule_skipped():
    job = _make_job(schedule="not-a-cron")
    config = _make_config([job])
    result = check_watchdog(config, {}, reference_time=datetime(2024, 6, 1, 12, 0))
    assert isinstance(result, WatchdogResult)
