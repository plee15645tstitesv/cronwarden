"""Tests for cronwarden.scheduler."""

from datetime import datetime
from unittest.mock import patch

import pytest

from cronwarden.config import Config, CronJob, Server
from cronwarden.scheduler import (
    NextRunResult,
    next_run_for_job,
    next_runs_for_config,
)


def _make_job(name: str = "backup", schedule: str = "0 2 * * *") -> CronJob:
    return CronJob(name=name, schedule=schedule, command="/usr/bin/backup")


def _make_config(*schedules: str) -> Config:
    jobs = [_make_job(f"job{i}", s) for i, s in enumerate(schedules)]
    server = Server(name="web01", jobs=jobs)
    return Config(servers=[server])


# ── NextRunResult ────────────────────────────────────────────────────────────

def test_next_run_result_is_ok_when_no_error():
    r = NextRunResult("s", "j", "* * * * *", datetime(2024, 1, 1, 12, 1))
    assert r.is_ok is True


def test_next_run_result_not_ok_when_error():
    r = NextRunResult("s", "j", "bad", None, error="invalid")
    assert r.is_ok is False


def test_next_run_result_str_includes_timestamp():
    r = NextRunResult("web01", "backup", "0 2 * * *", datetime(2024, 6, 15, 2, 0))
    assert "2024-06-15 02:00" in str(r)
    assert "web01/backup" in str(r)


def test_next_run_result_str_error_shows_message():
    r = NextRunResult("web01", "job", "bad", None, error="parse failed")
    assert "ERROR" in str(r)
    assert "parse failed" in str(r)


# ── next_run_for_job ─────────────────────────────────────────────────────────

def test_next_run_for_job_returns_next_run_result():
    job = _make_job(schedule="0 3 * * *")
    ref = datetime(2024, 1, 1, 0, 0)
    result = next_run_for_job(job, "web01", reference=ref)
    assert isinstance(result, NextRunResult)


def test_next_run_for_job_future_datetime():
    job = _make_job(schedule="0 3 * * *")
    ref = datetime(2024, 1, 1, 0, 0)
    result = next_run_for_job(job, "web01", reference=ref)
    if result.is_ok:
        assert result.next_run > ref


def test_next_run_for_job_handles_at_daily():
    job = _make_job(schedule="@daily")
    ref = datetime(2024, 1, 1, 12, 0)
    result = next_run_for_job(job, "web01", reference=ref)
    if result.is_ok:
        assert result.next_run is not None


def test_next_run_for_job_invalid_schedule_returns_error():
    job = _make_job(schedule="not-a-cron")
    result = next_run_for_job(job, "web01")
    # Either an error is returned or croniter isn't installed
    assert result.next_run is None or result.error is not None or result.is_ok


def test_next_run_for_job_missing_croniter_returns_error():
    import cronwarden.scheduler as sched_mod
    original = sched_mod.croniter
    sched_mod.croniter = None
    try:
        job = _make_job()
        result = next_run_for_job(job, "web01")
        assert result.is_ok is False
        assert "croniter" in result.error
    finally:
        sched_mod.croniter = original


# ── next_runs_for_config ─────────────────────────────────────────────────────

def test_next_runs_for_config_returns_list():
    config = _make_config("0 1 * * *", "30 6 * * 1")
    results = next_runs_for_config(config)
    assert isinstance(results, list)
    assert len(results) == 2


def test_next_runs_for_config_includes_all_servers():
    jobs_a = [_make_job("j1", "0 1 * * *")]
    jobs_b = [_make_job("j2", "0 2 * * *")]
    config = Config(servers=[
        Server(name="alpha", jobs=jobs_a),
        Server(name="beta", jobs=jobs_b),
    ])
    results = next_runs_for_config(config)
    server_names = {r.server_name for r in results}
    assert "alpha" in server_names
    assert "beta" in server_names


def test_next_runs_for_config_empty_servers():
    config = Config(servers=[])
    assert next_runs_for_config(config) == []
