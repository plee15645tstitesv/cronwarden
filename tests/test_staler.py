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


def test_job_updated_long_ago_is_stale():
    job = _make_job("old", last_updated="2023-01-01T00:00:00+00:00")
    config = _make_config(_make_server("web", [job]))
    result = find_stale_jobs(config, threshold_days=90, now=NOW)
    assert result.has_stale
    assert result.stale_jobs[0].days_since_update >= 90


def test_find_stale_jobs_respects_threshold():
    job = _make_job("borderline", last_updated="2024-03-03T00:00:00+00:00")  # ~90 days before NOW
    config = _make_config(_make_server("web", [job]))
    result_strict = find_stale_jobs(config, threshold_days=60, now=NOW)
    result_lenient = find_stale_jobs(config, threshold_days=120, now=NOW)
    assert result_strict.has_stale
    assert not result_lenient.has_stale


def test_find_stale_jobs_across_multiple_servers():
    s1 = _make_server("web", [_make_job("j1", last_updated="2020-01-01T00:00:00+00:00")])
    s2 = _make_server("db", [_make_job("j2", last_updated="2024-05-30T00:00:00+00:00")])
    config = _make_config(s1, s2)
    result = find_stale_jobs(config, threshold_days=90, now=NOW)
    assert result.total == 1
    assert result.stale_jobs[0].server_name == "web"
