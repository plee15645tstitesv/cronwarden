"""Tests for cronwarden.estimator."""

import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.estimator import (
    estimate_config,
    EstimationResult,
    JobEstimate,
    _runs_per_day,
    _estimate_seconds,
)


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup.sh", **kw) -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command, **kw)


def _make_config(*servers) -> Config:
    return Config(servers=list(servers))


# --- _runs_per_day ---

def test_runs_per_day_daily():
    assert _runs_per_day("@daily") == 1.0


def test_runs_per_day_hourly():
    assert _runs_per_day("@hourly") == 24.0


def test_runs_per_day_weekly():
    assert abs(_runs_per_day("@weekly") - 1 / 7) < 0.001


def test_runs_per_day_reboot_is_zero():
    assert _runs_per_day("@reboot") == 0.0


def test_runs_per_day_every_minute():
    # "* * * * *" — 60 minutes * 24 hours
    assert _runs_per_day("* * * * *") == 1440.0


def test_runs_per_day_once_a_day_fixed():
    assert _runs_per_day("0 3 * * *") == 1.0


def test_runs_per_day_every_6_hours():
    assert _runs_per_day("0 */6 * * *") == 4.0


# --- _estimate_seconds ---

def test_estimate_seconds_rsync():
    assert _estimate_seconds("rsync -av /src /dst") == 30


def test_estimate_seconds_mysqldump():
    assert _estimate_seconds("mysqldump -u root db > dump.sql") == 60


def test_estimate_seconds_curl():
    assert _estimate_seconds("curl https://example.com/health") == 5


def test_estimate_seconds_unknown_uses_default():
    assert _estimate_seconds("echo hello") == 3


# --- estimate_config ---

def test_estimate_config_returns_estimation_result():
    server = Server(name="web", jobs=[_make_job()])
    result = estimate_config(_make_config(server))
    assert isinstance(result, EstimationResult)


def test_estimate_config_total_matches_jobs():
    server = Server(name="web", jobs=[_make_job("j1"), _make_job("j2")])
    result = estimate_config(_make_config(server))
    assert result.total == 2


def test_estimate_config_is_empty_for_no_jobs():
    server = Server(name="empty", jobs=[])
    result = estimate_config(_make_config(server))
    assert result.is_empty


def test_estimate_config_total_seconds_sums_all():
    server = Server(name="web", jobs=[
        _make_job("a", schedule="@hourly", command="curl http://x"),
        _make_job("b", schedule="@daily", command="echo done"),
    ])
    result = estimate_config(_make_config(server))
    expected = (24 * 5) + (1 * 3)  # curl=5s * 24 + echo=3s * 1
    assert abs(result.total_seconds_per_day - expected) < 0.1


def test_job_estimate_summary_contains_name():
    server = Server(name="prod", jobs=[_make_job("nightly", schedule="@daily")])
    result = estimate_config(_make_config(server))
    assert "nightly" in result.estimates[0].summary()


def test_job_estimate_fields():
    server = Server(name="prod", jobs=[_make_job("sync", schedule="@daily", command="rsync /a /b")])
    result = estimate_config(_make_config(server))
    est = result.estimates[0]
    assert est.server == "prod"
    assert est.job_name == "sync"
    assert est.runs_per_day == 1.0
    assert est.estimated_seconds_per_run == 30


def test_multi_server_estimate_aggregates_correctly():
    s1 = Server(name="s1", jobs=[_make_job("a", schedule="@daily")])
    s2 = Server(name="s2", jobs=[_make_job("b", schedule="@daily")])
    result = estimate_config(_make_config(s1, s2))
    assert result.total == 2
    assert result.total_seconds_per_day == pytest.approx(6.0)  # 3s * 2
