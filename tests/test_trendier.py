"""Tests for cronwarden.trendier."""
from __future__ import annotations
from datetime import datetime
from unittest.mock import MagicMock
from cronwarden.config import CronJob, Server, Config
from cronwarden.historian import SnapshotEntry
from cronwarden.trendier import TrendPoint, TrendResult, build_trend


def _make_job(name: str = "job", schedule: str = "0 * * * *") -> CronJob:
    return CronJob(name=name, schedule=schedule, command="echo hi")


def _make_entry(label: str, jobs_per_server: int = 2, servers: int = 1) -> SnapshotEntry:
    server_list = [
        Server(name=f"srv{i}", host="localhost", jobs=[_make_job(f"j{j}") for j in range(jobs_per_server)])
        for i in range(servers)
    ]
    config = Config(servers=server_list)
    return SnapshotEntry(
        filename=f"{label}.json",
        label=label,
        created_at=datetime.utcnow(),
        config=config,
    )


def test_build_trend_returns_trend_result():
    entries = [_make_entry("snap1"), _make_entry("snap2")]
    result = build_trend(entries)
    assert isinstance(result, TrendResult)


def test_build_trend_empty_entries():
    result = build_trend([])
    assert result.is_empty
    assert result.total == 0


def test_build_trend_total_matches_entry_count():
    entries = [_make_entry(f"snap{i}") for i in range(3)]
    result = build_trend(entries)
    assert result.total == 3


def test_trend_point_total_jobs():
    entries = [_make_entry("snap1", jobs_per_server=4, servers=2)]
    result = build_trend(entries)
    assert result.points[0].total_jobs == 8


def test_trend_point_server_count():
    entries = [_make_entry("snap1", servers=3)]
    result = build_trend(entries)
    assert result.points[0].server_count == 3


def test_growing_when_jobs_increase():
    entries = [_make_entry("a", jobs_per_server=1), _make_entry("b", jobs_per_server=5)]
    result = build_trend(entries)
    assert result.growing is True


def test_shrinking_when_jobs_decrease():
    entries = [_make_entry("a", jobs_per_server=5), _make_entry("b", jobs_per_server=1)]
    result = build_trend(entries)
    assert result.growing is False


def test_stable_when_jobs_unchanged():
    entries = [_make_entry("a", jobs_per_server=3), _make_entry("b", jobs_per_server=3)]
    result = build_trend(entries)
    assert result.growing is None


def test_growing_returns_none_for_single_entry():
    result = build_trend([_make_entry("only")])
    assert result.growing is None


def test_peak_point_is_largest():
    entries = [_make_entry("a", 1), _make_entry("b", 10), _make_entry("c", 3)]
    result = build_trend(entries)
    assert result.peak_point is not None
    assert result.peak_point.label == "b"


def test_trend_point_summary_contains_label():
    point = TrendPoint(label="release-1", total_jobs=5, invalid_jobs=0, server_count=2)
    assert "release-1" in point.summary()


def test_trend_point_summary_contains_counts():
    point = TrendPoint(label="snap", total_jobs=7, invalid_jobs=2, server_count=3)
    s = point.summary()
    assert "7" in s
    assert "2" in s
    assert "3" in s
