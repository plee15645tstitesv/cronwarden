"""Tests for cronwarden.summarizer."""

import pytest

from cronwarden.config import Config, Server, CronJob
from cronwarden.summarizer import summarize, SummaryStats


def _make_job(name: str, schedule: str = "* * * * *", tags=None) -> CronJob:
    return CronJob(
        name=name,
        schedule=schedule,
        command=f"echo {name}",
        description=None,
        tags=tags or [],
    )


def _make_config(servers_jobs: dict) -> Config:
    """servers_jobs: {server_name: [CronJob, ...]}"""
    servers = [
        Server(name=sname, host=f"{sname}.example.com", jobs=jobs)
        for sname, jobs in servers_jobs.items()
    ]
    return Config(servers=servers)


def test_summarize_returns_summary_stats():
    config = _make_config({"web": [_make_job("backup")]})
    result = summarize(config)
    assert isinstance(result, SummaryStats)


def test_summarize_counts_servers():
    config = _make_config({"web": [_make_job("j1")], "db": [_make_job("j2")]})
    stats = summarize(config)
    assert stats.total_servers == 2


def test_summarize_counts_total_jobs():
    config = _make_config({"web": [_make_job("j1"), _make_job("j2")], "db": [_make_job("j3")]})
    stats = summarize(config)
    assert stats.total_jobs == 3


def test_summarize_all_valid_jobs():
    config = _make_config({"web": [_make_job("j1", "0 * * * *"), _make_job("j2", "@daily")]})
    stats = summarize(config)
    assert stats.valid_jobs == 2
    assert stats.invalid_jobs == 0


def test_summarize_detects_invalid_jobs():
    config = _make_config({"web": [_make_job("bad", "99 99 99 99 99")]})
    stats = summarize(config)
    assert stats.invalid_jobs == 1
    assert stats.valid_jobs == 0


def test_summarize_health_percent_all_valid():
    config = _make_config({"web": [_make_job("j1"), _make_job("j2")]})
    stats = summarize(config)
    assert stats.health_percent == 100.0


def test_summarize_health_percent_partial():
    config = _make_config({"web": [_make_job("ok", "@daily"), _make_job("bad", "99 99 99 99 99")]})
    stats = summarize(config)
    assert stats.health_percent == 50.0


def test_summarize_is_healthy_true():
    config = _make_config({"web": [_make_job("j1")]})
    stats = summarize(config)
    assert stats.is_healthy is True


def test_summarize_is_healthy_false():
    config = _make_config({"web": [_make_job("bad", "99 99 99 99 99")]})
    stats = summarize(config)
    assert stats.is_healthy is False


def test_summarize_servers_with_failures():
    config = _make_config({
        "web": [_make_job("ok", "@daily")],
        "db": [_make_job("bad", "99 99 99 99 99")],
    })
    stats = summarize(config)
    assert "db" in stats.servers_with_failures
    assert "web" not in stats.servers_with_failures


def test_summary_stats_str_healthy():
    stats = SummaryStats(total_servers=1, total_jobs=2, valid_jobs=2, invalid_jobs=0)
    output = str(stats)
    assert "HEALTHY" in output
    assert "100.0%" in output


def test_summary_stats_str_degraded():
    stats = SummaryStats(
        total_servers=2, total_jobs=3, valid_jobs=2, invalid_jobs=1,
        servers_with_failures=["db"]
    )
    output = str(stats)
    assert "DEGRADED" in output
    assert "db" in output
