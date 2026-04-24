"""Tests for cronwarden.throttler."""

import pytest

from cronwarden.config import Config, Server, CronJob
from cronwarden.throttler import check_throttle, ThrottledJob, ThrottleResult


def _make_job(name: str, schedule: str, command: str = "echo hi", tags=None) -> CronJob:
    return CronJob(
        name=name,
        schedule=schedule,
        command=command,
        description=None,
        tags=tags or [],
    )


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def _make_server(name: str, *jobs: CronJob) -> Server:
    return Server(name=name, host="localhost", jobs=list(jobs))


# ---------------------------------------------------------------------------
# ThrottleResult helpers
# ---------------------------------------------------------------------------

def test_throttle_result_has_throttled_false_when_empty():
    result = ThrottleResult()
    assert result.has_throttled is False


def test_throttle_result_has_throttled_true_when_populated():
    job = ThrottledJob(
        server="s", job_name="j", schedule="* * * * *",
        runs_per_day=1440.0, threshold=96.0, command="cmd"
    )
    result = ThrottleResult(throttled=[job], total_checked=1)
    assert result.has_throttled is True


def test_throttle_result_total():
    job = ThrottledJob(
        server="s", job_name="j", schedule="* * * * *",
        runs_per_day=1440.0, threshold=96.0, command="cmd"
    )
    result = ThrottleResult(throttled=[job, job], total_checked=2)
    assert result.total == 2


# ---------------------------------------------------------------------------
# ThrottledJob.summary
# ---------------------------------------------------------------------------

def test_throttled_job_summary_contains_name():
    job = ThrottledJob(
        server="web", job_name="poller", schedule="* * * * *",
        runs_per_day=1440.0, threshold=96.0, command="poll.sh"
    )
    assert "poller" in job.summary()
    assert "web" in job.summary()


# ---------------------------------------------------------------------------
# check_throttle
# ---------------------------------------------------------------------------

def test_check_throttle_returns_throttle_result():
    server = _make_server("prod", _make_job("daily", "0 0 * * *"))
    config = _make_config(server)
    result = check_throttle(config)
    assert isinstance(result, ThrottleResult)


def test_check_throttle_no_violations_for_infrequent_jobs():
    server = _make_server("prod", _make_job("daily", "0 0 * * *"))
    config = _make_config(server)
    result = check_throttle(config, max_runs_per_day=96.0)
    assert not result.has_throttled


def test_check_throttle_flags_every_minute_job():
    server = _make_server("prod", _make_job("minutely", "* * * * *"))
    config = _make_config(server)
    result = check_throttle(config, max_runs_per_day=96.0)
    assert result.has_throttled
    assert result.total == 1
    assert result.throttled[0].job_name == "minutely"


def test_check_throttle_counts_total_checked():
    server = _make_server(
        "prod",
        _make_job("j1", "0 * * * *"),
        _make_job("j2", "* * * * *"),
    )
    config = _make_config(server)
    result = check_throttle(config, max_runs_per_day=96.0)
    assert result.total_checked == 2


def test_check_throttle_tag_filter_skips_untagged():
    server = _make_server(
        "prod",
        _make_job("minutely", "* * * * *", tags=[]),
    )
    config = _make_config(server)
    result = check_throttle(config, max_runs_per_day=96.0, tag="critical")
    assert not result.has_throttled


def test_check_throttle_tag_filter_includes_matching_tag():
    server = _make_server(
        "prod",
        _make_job("minutely", "* * * * *", tags=["critical"]),
    )
    config = _make_config(server)
    result = check_throttle(config, max_runs_per_day=96.0, tag="critical")
    assert result.has_throttled


def test_check_throttle_custom_threshold():
    # Every 30 min = 48 runs/day; with threshold=24 it should flag
    server = _make_server("prod", _make_job("half-hourly", "*/30 * * * *"))
    config = _make_config(server)
    result = check_throttle(config, max_runs_per_day=24.0)
    assert result.has_throttled
    assert result.throttled[0].threshold == 24.0
