"""Unit tests for cronwarden.outlier."""

import pytest
from cronwarden.outlier import (
    find_outliers,
    OutlierJob,
    OutlierResult,
    _detect_outliers,
)
from cronwarden.config import Config, Server, CronJob


def _make_job(name: str, schedule: str) -> CronJob:
    return CronJob(name=name, schedule=schedule, command=f"run-{name}")


def _make_config(*servers) -> Config:
    return Config(servers=list(servers))


def _make_server(name: str, *jobs) -> Server:
    return Server(name=name, jobs=list(jobs))


# --- OutlierResult ---

def test_outlier_result_has_outliers_false_when_empty():
    r = OutlierResult()
    assert not r.has_outliers


def test_outlier_result_has_outliers_true_when_populated():
    o = OutlierJob("s", "j", "* * * * *", "reason", "high")
    r = OutlierResult(outliers=[o])
    assert r.has_outliers


def test_outlier_result_total():
    outliers = [
        OutlierJob("s", "j1", "* * * * *", "r", "high"),
        OutlierJob("s", "j2", "*/2 * * * *", "r", "medium"),
    ]
    r = OutlierResult(outliers=outliers)
    assert r.total == 2


def test_outlier_result_by_severity_filters_correctly():
    outliers = [
        OutlierJob("s", "j1", "* * * * *", "r", "high"),
        OutlierJob("s", "j2", "*/5 * * * *", "r", "medium"),
        OutlierJob("s", "j3", "37 * * * *", "r", "low"),
    ]
    r = OutlierResult(outliers=outliers)
    assert len(r.by_severity("high")) == 1
    assert len(r.by_severity("medium")) == 1
    assert len(r.by_severity("low")) == 1


# --- _detect_outliers ---

def test_every_minute_is_high_severity():
    found = _detect_outliers("srv", "job", "* * * * *")
    assert len(found) == 1
    assert found[0].severity == "high"


def test_step_two_minutes_is_medium():
    found = _detect_outliers("srv", "job", "*/2 * * * *")
    assert len(found) == 1
    assert found[0].severity == "medium"


def test_step_ten_minutes_is_not_flagged():
    found = _detect_outliers("srv", "job", "*/10 * * * *")
    assert len(found) == 0


def test_unusual_minute_is_low_severity():
    found = _detect_outliers("srv", "job", "37 * * * *")
    assert len(found) == 1
    assert found[0].severity == "low"


def test_common_minute_not_flagged():
    found = _detect_outliers("srv", "job", "0 * * * *")
    assert len(found) == 0


def test_special_schedule_not_flagged():
    found = _detect_outliers("srv", "job", "@daily")
    assert len(found) == 0


def test_invalid_parts_not_flagged():
    # Only 3 parts — should return empty gracefully
    found = _detect_outliers("srv", "job", "* * *")
    assert found == []


# --- find_outliers ---

def test_find_outliers_returns_outlier_result():
    config = _make_config(_make_server("web", _make_job("backup", "0 2 * * *")))
    result = find_outliers(config)
    assert isinstance(result, OutlierResult)


def test_find_outliers_no_outliers_for_clean_config():
    config = _make_config(
        _make_server("web",
                     _make_job("backup", "0 2 * * *"),
                     _make_job("cleanup", "30 3 * * 0"))
    )
    result = find_outliers(config)
    assert not result.has_outliers


def test_find_outliers_detects_every_minute_job():
    config = _make_config(_make_server("web", _make_job("poller", "* * * * *")))
    result = find_outliers(config)
    assert result.has_outliers
    assert result.outliers[0].severity == "high"


def test_find_outliers_multi_server():
    config = _make_config(
        _make_server("s1", _make_job("j1", "* * * * *")),
        _make_server("s2", _make_job("j2", "*/3 * * * *")),
    )
    result = find_outliers(config)
    assert result.total == 2
