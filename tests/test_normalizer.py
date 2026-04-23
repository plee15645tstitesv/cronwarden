"""Tests for cronwarden.normalizer."""

import pytest
from cronwarden.normalizer import (
    normalize_config,
    _normalize_schedule,
    NormalizationResult,
    NormalizedJob,
)
from cronwarden.config import Config, Server, CronJob


def _make_job(name: str, schedule: str) -> CronJob:
    return CronJob(name=name, schedule=schedule, command=f"run {name}")


def _make_config(*pairs) -> Config:
    """pairs: (server_name, [(job_name, schedule), ...])"""
    servers = []
    for server_name, jobs in pairs:
        servers.append(
            Server(name=server_name, jobs=[_make_job(n, s) for n, s in jobs])
        )
    return Config(servers=servers)


def test_normalize_config_returns_normalization_result():
    config = _make_config(("web", [("backup", "0 0 * * *")]))
    result = normalize_config(config)
    assert isinstance(result, NormalizationResult)


def test_normalize_config_total_matches_jobs():
    config = _make_config(
        ("web", [("job1", "@daily"), ("job2", "0 * * * *")])
    )
    result = normalize_config(config)
    assert result.total == 2


def test_alias_daily_is_normalized():
    schedule, changed = _normalize_schedule("@daily")
    assert schedule == "0 0 * * *"
    assert changed is True


def test_alias_hourly_is_normalized():
    schedule, changed = _normalize_schedule("@hourly")
    assert schedule == "0 * * * *"
    assert changed is True


def test_alias_weekly_is_normalized():
    schedule, changed = _normalize_schedule("@weekly")
    assert schedule == "0 0 * * 0"
    assert changed is True


def test_alias_monthly_is_normalized():
    schedule, changed = _normalize_schedule("@monthly")
    assert schedule == "0 0 1 * *"
    assert changed is True


def test_alias_yearly_and_annually_match():
    s1, _ = _normalize_schedule("@yearly")
    s2, _ = _normalize_schedule("@annually")
    assert s1 == s2


def test_standard_schedule_unchanged():
    schedule, changed = _normalize_schedule("0 0 * * *")
    assert schedule == "0 0 * * *"
    assert changed is False


def test_extra_whitespace_is_normalized():
    schedule, changed = _normalize_schedule("0  0   *  *  *")
    assert schedule == "0 0 * * *"
    assert changed is True


def test_has_changes_false_when_all_canonical():
    config = _make_config(("srv", [("j", "0 0 * * *")]))
    result = normalize_config(config)
    assert result.has_changes is False


def test_has_changes_true_when_alias_present():
    config = _make_config(("srv", [("j", "@daily")]))
    result = normalize_config(config)
    assert result.has_changes is True


def test_total_changed_counts_correctly():
    config = _make_config(
        ("srv", [("j1", "@daily"), ("j2", "0 0 * * *"), ("j3", "@hourly")])
    )
    result = normalize_config(config)
    assert result.total_changed == 2


def test_changed_jobs_returns_only_changed():
    config = _make_config(
        ("srv", [("j1", "@daily"), ("j2", "0 0 * * *")])
    )
    result = normalize_config(config)
    changed = result.changed_jobs()
    assert len(changed) == 1
    assert changed[0].job_name == "j1"


def test_normalized_job_summary_changed():
    job = NormalizedJob(
        server="web",
        job_name="backup",
        original_schedule="@daily",
        normalized_schedule="0 0 * * *",
        was_changed=True,
    )
    s = job.summary()
    assert "@daily" in s
    assert "0 0 * * *" in s
    assert "->" in s


def test_normalized_job_summary_unchanged():
    job = NormalizedJob(
        server="web",
        job_name="backup",
        original_schedule="0 0 * * *",
        normalized_schedule="0 0 * * *",
        was_changed=False,
    )
    s = job.summary()
    assert "unchanged" in s
