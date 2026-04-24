"""Tests for cronwarden.cycler."""
import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.cycler import CycleEntry, CycleResult, detect_cycles, _schedules_overlap


def _make_job(name: str, schedule: str, command: str = "echo hi") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def _make_server(name: str, jobs: list) -> Server:
    return Server(name=name, host="localhost", jobs=jobs)


# --- Unit: CycleResult ---

def test_cycle_result_has_cycles_false_when_empty():
    r = CycleResult()
    assert r.has_cycles is False


def test_cycle_result_has_cycles_true_when_populated():
    entry = CycleEntry(
        server="s", job_name="j", schedule="* * * * *",
        overlap_with="* * * * *", overlap_job="j2", reason="both run every minute"
    )
    r = CycleResult(entries=[entry])
    assert r.has_cycles is True


def test_cycle_result_total():
    entries = [
        CycleEntry("s", "j1", "0 1 * * *", "0 1 * * *", "j2", "same execution time (01:00)"),
        CycleEntry("s", "j3", "* * * * *", "* * * * *", "j4", "both run every minute"),
    ]
    r = CycleResult(entries=entries)
    assert r.total == 2


# --- Unit: CycleEntry.summary ---

def test_cycle_entry_summary_contains_job_name():
    e = CycleEntry(
        server="web", job_name="backup", schedule="0 2 * * *",
        overlap_with="0 2 * * *", overlap_job="sync", reason="same execution time (02:00)"
    )
    s = e.summary()
    assert "backup" in s
    assert "sync" in s
    assert "web" in s


# --- Unit: _schedules_overlap ---

def test_identical_schedules_overlap():
    reason = _schedules_overlap("0 3 * * *", "0 3 * * *")
    assert reason is not None
    assert "identical" in reason


def test_different_schedules_no_overlap():
    reason = _schedules_overlap("0 1 * * *", "0 2 * * *")
    assert reason is None


def test_both_every_minute_overlap():
    reason = _schedules_overlap("* * * * *", "* * * * *")
    assert reason is not None
    assert "every minute" in reason


def test_same_fixed_time_overlap():
    reason = _schedules_overlap("30 6 * * *", "30 6 * * 1")
    assert reason is not None
    assert "06:30" in reason


# --- Integration: detect_cycles ---

def test_no_cycles_when_all_unique_schedules():
    server = _make_server("prod", [
        _make_job("a", "0 1 * * *"),
        _make_job("b", "0 2 * * *"),
        _make_job("c", "0 3 * * *"),
    ])
    result = detect_cycles(_make_config(server))
    assert result.has_cycles is False
    assert result.total == 0


def test_detects_identical_schedule_on_same_server():
    server = _make_server("prod", [
        _make_job("job1", "0 4 * * *"),
        _make_job("job2", "0 4 * * *"),
    ])
    result = detect_cycles(_make_config(server))
    assert result.has_cycles is True
    assert result.total >= 1


def test_detects_overlap_across_servers():
    s1 = _make_server("alpha", [_make_job("nightly", "0 0 * * *")])
    s2 = _make_server("beta", [_make_job("midnight", "0 0 * * *")])
    result = detect_cycles(_make_config(s1, s2))
    assert result.has_cycles is True


def test_no_cycles_empty_config():
    result = detect_cycles(_make_config())
    assert result.has_cycles is False
    assert result.total == 0


def test_cycle_entry_fields_are_correct():
    server = _make_server("srv", [
        _make_job("first", "15 10 * * *"),
        _make_job("second", "15 10 * * *"),
    ])
    result = detect_cycles(_make_config(server))
    assert result.has_cycles is True
    entry = result.entries[0]
    assert entry.server == "srv"
    assert entry.job_name == "second"
    assert entry.overlap_job == "first"
