"""Tests for cronwarden/cadencer.py"""

import pytest
from cronwarden.cadencer import (
    check_cadence,
    CadenceResult,
    CadenceIssue,
    _parse_minute,
    _min_gap_minutes,
)
from cronwarden.config import Config, Server, CronJob


def _make_job(name: str, schedule: str, command: str = "echo hi") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def _make_server(name: str, *jobs: CronJob) -> Server:
    return Server(name=name, host="localhost", jobs=list(jobs))


# --- unit: _parse_minute ---

def test_parse_minute_wildcard():
    assert _parse_minute("*") == list(range(60))


def test_parse_minute_single():
    assert _parse_minute("30") == [30]


def test_parse_minute_list():
    assert _parse_minute("0,15,30,45") == [0, 15, 30, 45]


def test_parse_minute_step():
    assert _parse_minute("*/10") == [0, 10, 20, 30, 40, 50]


def test_parse_minute_range():
    assert _parse_minute("0-4") == [0, 1, 2, 3, 4]


# --- unit: _min_gap_minutes ---

def test_min_gap_every_minute():
    assert _min_gap_minutes("* * * * *") == 1


def test_min_gap_every_10_minutes():
    assert _min_gap_minutes("*/10 * * * *") == 10


def test_min_gap_single_minute_returns_60():
    assert _min_gap_minutes("30 * * * *") == 60


def test_min_gap_special_schedule_returns_60():
    assert _min_gap_minutes("@daily") == 60


# --- check_cadence ---

def test_check_cadence_returns_cadence_result():
    config = _make_config(_make_server("s1", _make_job("j1", "0 * * * *")))
    result = check_cadence(config)
    assert isinstance(result, CadenceResult)


def test_clean_config_has_no_issues():
    config = _make_config(
        _make_server(
            "prod",
            _make_job("backup", "0 2 * * *"),
            _make_job("report", "0 6 * * 1"),
        )
    )
    result = check_cadence(config)
    assert not result.has_issues
    assert result.total == 0


def test_every_minute_job_is_flagged():
    config = _make_config(_make_server("prod", _make_job("poller", "* * * * *")))
    result = check_cadence(config)
    assert result.has_issues
    assert result.total == 1
    assert "prod" in result.issues[0].server
    assert "poller" in result.issues[0].job_name


def test_every_minute_issue_contains_runs_per_day():
    config = _make_config(_make_server("s", _make_job("j", "* * * * *")))
    result = check_cadence(config)
    assert result.issues[0].runs_per_day > 0


def test_close_interval_job_is_flagged():
    # every 2 minutes via list
    config = _make_config(
        _make_server("s", _make_job("j", "0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58 * * * *"))
    )
    result = check_cadence(config)
    assert result.has_issues


def test_issue_summary_is_string():
    config = _make_config(_make_server("prod", _make_job("tick", "* * * * *")))
    result = check_cadence(config)
    assert isinstance(result.issues[0].summary(), str)
    assert "prod" in result.issues[0].summary()


def test_multiple_servers_each_checked():
    config = _make_config(
        _make_server("s1", _make_job("j1", "* * * * *")),
        _make_server("s2", _make_job("j2", "* * * * *")),
    )
    result = check_cadence(config)
    assert result.total == 2
    servers = {i.server for i in result.issues}
    assert "s1" in servers
    assert "s2" in servers
