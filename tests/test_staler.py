"""Tests for cronwarden.staler — stale job detection."""

from datetime import datetime, timezone

import pytest

from cronwarden.config import Config, CronJob, Server
from cronwarden.staler import StalenessResult, StaleJob, find_stale_jobs, _days_since


NOW = datetime(2024, 6, 1, tzinfo=timezone.utc)


def _make_job(name: str, last_updated: str = None, **kwargs) -> CronJob:
    data = dict(
        name=name,
        schedule="0 * * * *",
        command=f"run_{name}.sh",
        description="A test job",
    )
    if last_updated is not None:
        data["last_updated"] = last_updated
    data.update(kwargs)
    return CronJob(**data)


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def _make_server(name: str, jobs: list) -> Server:
    return Server(name=name, host=f"{name}.example.com", jobs=jobs)


# --- StalenessResult ---

def test_staleness_result_has_stale_false_when_empty():
    result = StalenessResult()
    assert result.has_stale is False


def test_staleness_result_has_stale_true_when_populated():
    job = _make_job("backup")
    entry = StaleJob(server_name="web", job=job, days_since_update=None)
    result = StalenessResult(stale_jobs=[entry])
    assert result.has_stale is True


def test_staleness_result_total():
    jobs = [StaleJob("s", _make_job(f"j{i}"), None) for i in range(3)]
    result = StalenessResult(stale_jobs=jobs)
    assert result.total == 3


def test_staleness_result_str_empty():
    result = StalenessResult()
    assert "No stale jobs" in str(result)


def test_staleness_result_str_lists_jobs():
    job = _make_job("cleanup")
    entry = StaleJob(server_name="prod", job=job, days_since_update=120)
    result = StalenessResult(stale_jobs=[entry])
    text = str(result)
    assert "cleanup" in text
    assert "prod" in text
    assert "120" in text


# --- _days_since ---

def test_days_since_recent_date():
    days = _days_since("2024-05-01T00:00:00+00:00", NOW)
    assert days == 31


def test_days_since_invalid_returns_none():
    assert _days_since("not-a-date", NOW) is None


def test_days_since_naive_datetime_treated_as_utc():
    days = _days_since("2024-05-01T00:00:00", NOW)
    assert days == 31


def test_days_since_same_day_returns_zero():
    days = _days_since("2024-06-01T00:00:00+00:00", NOW)
    assert days == 0


def test_days_since_future_date_returns_negative():
    days = _days_since("2024-06-15T00:00:00+00:00", NOW)
    assert days == -14


# --- find_stale_jobs ---

def test_find_stale_jobs_returns_staleness_result():
    config = _make_config(_make_server("web", [_make_job("j1")]))
    result = find_stale_jobs(config, threshold_days=90, now=NOW)
    assert isinstance(result, StalenessResult)


def test_job_without_last_updated_is_stale():
    job = _make_job("orphan")
    config = _make_config(_make_server("web", [job]))
    result = find_stale_jobs(config, threshold_days=90, now=NOW)
    assert result.has_stale
    assert result.stale_jobs[0].days_since_update is None


def test_job_updated_recently_is_not_stale():
    job = _make_job("fresh", last_updated="2024-05-25T00:00:00+00:00")
    config = _make_config(_make_server("web", [job]))
    result = find_stale_jobs(config, threshold_days=90, now=NOW)
    assert not result.has_stale


def test_job_updated_exactly_at_threshold_is_not_stale():
    # A job updated exactly threshold_days ago should not be considered stale.
    job = _make_job("borderline", last_updated="2024-03-03T00:00:00+00:00")  # 90 days before NOW
    config = _make_config(_make_server("web", [job]))
    result = find_stale_jobs(config, threshold_days=90, now=NOW)
    assert not result.has_stale


def test_job_updated_over_threshold_is_stale():
    job = _make_job("old", last_updated="2024-01-01T00:00:00+00:00")  # ~152 days before NOW
    config = _make_config(_make_server("web", [job]))
    result = find_stale_jobs(config, threshold_days=90, now=NOW)
    assert result.has_stale
    assert result.stale_jobs[0].days_since_update == 152
