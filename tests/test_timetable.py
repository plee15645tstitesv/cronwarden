"""Tests for cronwarden.timetable."""

import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.timetable import build_timetable, TimetableResult, TimetableEntry, _parse_hour_field


def _make_job(name: str, schedule: str, tags=None) -> CronJob:
    return CronJob(name=name, schedule=schedule, command=f"run_{name}", tags=tags or [])


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def _make_server(name: str, *jobs: CronJob) -> Server:
    return Server(name=name, host=f"{name}.example.com", jobs=list(jobs))


# --- _parse_hour_field ---

def test_parse_hour_wildcard_returns_all_hours():
    assert _parse_hour_field("*") == list(range(24))


def test_parse_hour_single_value():
    assert _parse_hour_field("3") == [3]


def test_parse_hour_comma_list():
    assert _parse_hour_field("6,12,18") == [6, 12, 18]


def test_parse_hour_range():
    assert _parse_hour_field("8-10") == [8, 9, 10]


def test_parse_hour_step():
    assert _parse_hour_field("*/6") == [0, 6, 12, 18]


# --- build_timetable ---

def test_build_timetable_returns_timetable_result():
    job = _make_job("backup", "0 2 * * *")
    server = _make_server("web", job)
    result = build_timetable(_make_config(server))
    assert isinstance(result, TimetableResult)


def test_build_timetable_total_matches_job_count():
    jobs = [_make_job(f"job{i}", "0 * * * *") for i in range(3)]
    server = _make_server("srv", *jobs)
    result = build_timetable(_make_config(server))
    assert result.total == 3


def test_build_timetable_is_empty_false_when_jobs_present():
    job = _make_job("nightly", "0 0 * * *")
    server = _make_server("app", job)
    result = build_timetable(_make_config(server))
    assert not result.is_empty


def test_build_timetable_is_empty_true_when_no_jobs():
    server = _make_server("empty")
    result = build_timetable(_make_config(server))
    assert result.is_empty


def test_daily_alias_maps_to_hour_zero():
    job = _make_job("daily", "@daily")
    server = _make_server("s", job)
    result = build_timetable(_make_config(server))
    assert result.entries[0].hours == [0]


def test_hourly_alias_maps_to_all_hours():
    job = _make_job("poll", "@hourly")
    server = _make_server("s", job)
    result = build_timetable(_make_config(server))
    assert result.entries[0].hours == list(range(24))


def test_reboot_alias_has_no_hours():
    job = _make_job("init", "@reboot")
    server = _make_server("s", job)
    result = build_timetable(_make_config(server))
    assert result.entries[0].hours == []


def test_grid_populated_for_matching_hours():
    job = _make_job("report", "0 9 * * *")
    server = _make_server("s", job)
    result = build_timetable(_make_config(server))
    assert 9 in result.grid
    assert any("report" in label for label in result.grid[9])


def test_busiest_hour_returns_correct_hour():
    j1 = _make_job("a", "0 6 * * *")
    j2 = _make_job("b", "0 6 * * *")
    j3 = _make_job("c", "0 12 * * *")
    server = _make_server("s", j1, j2, j3)
    result = build_timetable(_make_config(server))
    assert result.busiest_hour() == 6


def test_busiest_hour_none_when_empty():
    server = _make_server("s")
    result = build_timetable(_make_config(server))
    assert result.busiest_hour() is None


def test_entry_summary_contains_job_name():
    job = _make_job("cleanup", "30 3 * * *")
    server = _make_server("s", job)
    result = build_timetable(_make_config(server))
    assert "cleanup" in result.entries[0].summary()


def test_multi_server_entries_attributed_correctly():
    j1 = _make_job("job1", "0 1 * * *")
    j2 = _make_job("job2", "0 2 * * *")
    s1 = _make_server("alpha", j1)
    s2 = _make_server("beta", j2)
    result = build_timetable(_make_config(s1, s2))
    servers = {e.server for e in result.entries}
    assert "alpha" in servers
    assert "beta" in servers
