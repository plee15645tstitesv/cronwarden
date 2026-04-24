"""Tests for cronwarden.heatmap."""

import pytest

from cronwarden.config import Config, CronJob, Server
from cronwarden.heatmap import (
    HeatmapCell,
    HeatmapResult,
    _parse_field,
    build_heatmap,
)


def _make_job(name: str, schedule: str) -> CronJob:
    return CronJob(name=name, schedule=schedule, command=f"echo {name}")


def _make_config(*schedules: str) -> Config:
    jobs = [_make_job(f"job{i}", s) for i, s in enumerate(schedules)]
    server = Server(name="web1", host="localhost", jobs=jobs)
    return Config(servers=[server])


# --- _parse_field ---

def test_parse_field_wildcard():
    assert _parse_field("*") == [-1]


def test_parse_field_single_value():
    assert _parse_field("5") == [5]


def test_parse_field_comma_list():
    assert _parse_field("1,2,3") == [1, 2, 3]


def test_parse_field_range():
    assert _parse_field("2-4") == [2, 3, 4]


def test_parse_field_step_returns_wildcard():
    assert _parse_field("*/5") == [-1]


# --- HeatmapResult ---

def test_heatmap_result_is_empty_when_no_cells():
    r = HeatmapResult(cells=[], total_jobs=0)
    assert r.is_empty()


def test_heatmap_result_not_empty_when_cells_present():
    r = HeatmapResult(cells=[HeatmapCell(hour=2, dow=1, count=3)], total_jobs=1)
    assert not r.is_empty()


def test_peak_cell_returns_highest_count():
    cells = [
        HeatmapCell(hour=1, dow=0, count=2),
        HeatmapCell(hour=2, dow=0, count=5),
        HeatmapCell(hour=3, dow=0, count=1),
    ]
    r = HeatmapResult(cells=cells, total_jobs=3)
    assert r.peak_cell().count == 5


def test_peak_cell_none_when_empty():
    r = HeatmapResult(cells=[], total_jobs=0)
    assert r.peak_cell() is None


def test_to_dict_contains_total_jobs():
    r = HeatmapResult(cells=[], total_jobs=7)
    assert r.to_dict()["total_jobs"] == 7


def test_to_dict_cells_serialized():
    cells = [HeatmapCell(hour=3, dow=2, count=4)]
    r = HeatmapResult(cells=cells, total_jobs=4)
    d = r.to_dict()
    assert d["cells"][0] == {"hour": 3, "dow": 2, "count": 4}


# --- build_heatmap ---

def test_build_heatmap_returns_heatmap_result():
    config = _make_config("0 2 * * *")
    result = build_heatmap(config)
    assert isinstance(result, HeatmapResult)


def test_build_heatmap_counts_total_jobs():
    config = _make_config("0 2 * * *", "30 4 * * 1")
    result = build_heatmap(config)
    assert result.total_jobs == 2


def test_build_heatmap_specific_hour_and_dow():
    config = _make_config("0 6 * * 3")
    result = build_heatmap(config)
    assert any(c.hour == 6 and c.dow == 3 and c.count == 1 for c in result.cells)


def test_build_heatmap_wildcard_dow_uses_minus_one():
    config = _make_config("0 8 * * *")
    result = build_heatmap(config)
    assert any(c.hour == 8 and c.dow == -1 for c in result.cells)


def test_build_heatmap_special_schedule_uses_minus_one():
    config = _make_config("@daily")
    result = build_heatmap(config)
    assert any(c.hour == -1 and c.dow == -1 for c in result.cells)


def test_build_heatmap_accumulates_counts():
    config = _make_config("0 3 * * *", "0 3 * * *")
    result = build_heatmap(config)
    cell = next(c for c in result.cells if c.hour == 3)
    assert cell.count == 2
