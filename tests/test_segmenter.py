"""Tests for cronwarden.segmenter."""

import pytest
from cronwarden.segmenter import (
    segment_config,
    _classify_schedule,
    SegmentResult,
    SegmentEntry,
    SEGMENT_LABELS,
)
from cronwarden.config import Config, Server, CronJob


def _make_job(name: str, schedule: str, **kwargs) -> CronJob:
    return CronJob(name=name, schedule=schedule, command=f"run_{name}", **kwargs)


def _make_config(*servers) -> Config:
    return Config(servers=list(servers))


def _make_server(name: str, *jobs) -> Server:
    return Server(name=name, host=f"{name}.example.com", jobs=list(jobs))


# --- _classify_schedule ---

def test_classify_hourly_wildcard():
    assert _classify_schedule("* * * * *") == "hourly"


def test_classify_daily_fixed_time():
    assert _classify_schedule("0 2 * * *") == "daily"


def test_classify_weekly_by_dow():
    assert _classify_schedule("0 3 * * 1") == "weekly"


def test_classify_monthly_by_dom():
    assert _classify_schedule("0 4 15 * *") == "monthly"


def test_classify_other_for_specific_month():
    assert _classify_schedule("0 0 1 1 *") == "other"


def test_classify_special_hourly():
    assert _classify_schedule("@hourly") == "hourly"


def test_classify_special_daily():
    assert _classify_schedule("@daily") == "daily"


def test_classify_special_midnight():
    assert _classify_schedule("@midnight") == "daily"


def test_classify_special_weekly():
    assert _classify_schedule("@weekly") == "weekly"


def test_classify_special_monthly():
    assert _classify_schedule("@monthly") == "monthly"


def test_classify_special_reboot():
    assert _classify_schedule("@reboot") == "other"


def test_classify_invalid_schedule_returns_other():
    assert _classify_schedule("not-a-cron") == "other"


# --- segment_config ---

def test_segment_config_returns_segment_result():
    config = _make_config(_make_server("web", _make_job("j1", "0 1 * * *")))
    result = segment_config(config)
    assert isinstance(result, SegmentResult)


def test_segment_result_contains_all_labels():
    config = _make_config(_make_server("web", _make_job("j1", "0 1 * * *")))
    result = segment_config(config)
    for label in SEGMENT_LABELS:
        assert label in result.buckets


def test_segment_total_matches_all_jobs():
    server = _make_server(
        "web",
        _make_job("j1", "0 1 * * *"),
        _make_job("j2", "* * * * *"),
        _make_job("j3", "0 0 1 * *"),
    )
    config = _make_config(server)
    result = segment_config(config)
    assert result.total == 3


def test_daily_job_in_daily_bucket():
    server = _make_server("web", _make_job("backup", "0 2 * * *"))
    config = _make_config(server)
    result = segment_config(config)
    assert len(result.jobs_in_segment("daily")) == 1
    assert result.jobs_in_segment("daily")[0].job_name == "backup"


def test_empty_config_returns_empty_result():
    config = _make_config()
    result = segment_config(config)
    assert result.is_empty()
    assert result.total == 0


def test_segment_entry_summary_format():
    entry = SegmentEntry(server="web", job_name="sync", schedule="0 * * * *", segment="hourly")
    s = entry.summary()
    assert "hourly" in s
    assert "web" in s
    assert "sync" in s


def test_segment_counts_returns_dict():
    server = _make_server(
        "web",
        _make_job("j1", "0 1 * * *"),
        _make_job("j2", "0 2 * * *"),
        _make_job("j3", "* * * * *"),
    )
    config = _make_config(server)
    result = segment_config(config)
    counts = result.segment_counts()
    assert counts["daily"] == 2
    assert counts["hourly"] == 1
