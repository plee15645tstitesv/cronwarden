"""Tests for cronwarden.drifter."""
import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.drifter import detect_drift, DriftedJob, DriftResult


def _make_job(name, schedule="0 * * * *", command="echo hi", tags=None):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [])


def _make_config(*servers):
    return Config(servers=list(servers))


def _make_server(name, jobs):
    return Server(name=name, host="localhost", jobs=jobs)


# ---- DriftResult unit tests ----

def test_drift_result_has_drift_false_when_empty():
    r = DriftResult()
    assert not r.has_drift


def test_drift_result_has_drift_true_when_populated():
    r = DriftResult(drifted=[DriftedJob("s", "j", "0 * * * *", "5 * * * *")])
    assert r.has_drift


def test_drift_result_total_matches_drifted_count():
    r = DriftResult(drifted=[
        DriftedJob("s", "j1", "0 * * * *", "5 * * * *"),
        DriftedJob("s", "j2", "@daily", "@hourly"),
    ])
    assert r.total == 2


# ---- DriftedJob.summary ----

def test_drifted_job_summary_contains_server_and_name():
    d = DriftedJob("web", "backup", "0 2 * * *", "0 3 * * *")
    s = d.summary()
    assert "web" in s
    assert "backup" in s
    assert "0 2 * * *" in s
    assert "0 3 * * *" in s


# ---- detect_drift integration with snapshotter ----

def test_no_drift_when_schedules_identical(tmp_path):
    from cronwarden.snapshotter import save_snapshot
    cfg = _make_config(_make_server("prod", [_make_job("nightly", "0 2 * * *")]))
    snap = str(tmp_path / "snap.json")
    save_snapshot(cfg, snap)
    result = detect_drift(cfg, snap)
    assert not result.has_drift
    assert result.total == 0


def test_drift_detected_when_schedule_changes(tmp_path):
    from cronwarden.snapshotter import save_snapshot
    baseline_cfg = _make_config(_make_server("prod", [_make_job("nightly", "0 2 * * *")]))
    snap = str(tmp_path / "snap.json")
    save_snapshot(baseline_cfg, snap)
    current_cfg = _make_config(_make_server("prod", [_make_job("nightly", "0 3 * * *")]))
    result = detect_drift(current_cfg, snap)
    assert result.has_drift
    assert result.total == 1
    assert result.drifted[0].baseline_schedule == "0 2 * * *"
    assert result.drifted[0].current_schedule == "0 3 * * *"


def test_new_job_appears_in_missing_in_baseline(tmp_path):
    from cronwarden.snapshotter import save_snapshot
    baseline_cfg = _make_config(_make_server("prod", [_make_job("nightly", "0 2 * * *")]))
    snap = str(tmp_path / "snap.json")
    save_snapshot(baseline_cfg, snap)
    current_cfg = _make_config(_make_server("prod", [
        _make_job("nightly", "0 2 * * *"),
        _make_job("hourly", "0 * * * *"),
    ]))
    result = detect_drift(current_cfg, snap)
    assert not result.has_drift
    assert "prod/hourly" in result.missing_in_baseline


def test_removed_job_appears_in_missing_in_current(tmp_path):
    from cronwarden.snapshotter import save_snapshot
    baseline_cfg = _make_config(_make_server("prod", [
        _make_job("nightly", "0 2 * * *"),
        _make_job("hourly", "0 * * * *"),
    ]))
    snap = str(tmp_path / "snap.json")
    save_snapshot(baseline_cfg, snap)
    current_cfg = _make_config(_make_server("prod", [_make_job("nightly", "0 2 * * *")]))
    result = detect_drift(current_cfg, snap)
    assert "prod/hourly" in result.missing_in_current
