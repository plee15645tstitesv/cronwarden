"""Integration tests for the segmenter using realistic config structures."""

import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.segmenter import segment_config


def _job(name, schedule):
    return CronJob(name=name, schedule=schedule, command=f"/bin/{name}")


def _server(name, *jobs):
    return Server(name=name, host=f"{name}.host", jobs=list(jobs))


def test_integration_multi_server_total_correct():
    config = Config(servers=[
        _server("web", _job("j1", "0 1 * * *"), _job("j2", "* * * * *")),
        _server("db", _job("j3", "0 0 1 * *"), _job("j4", "@weekly")),
    ])
    result = segment_config(config)
    assert result.total == 4


def test_integration_special_aliases_bucketed_correctly():
    config = Config(servers=[
        _server("app",
            _job("a", "@hourly"),
            _job("b", "@daily"),
            _job("c", "@weekly"),
            _job("d", "@monthly"),
            _job("e", "@reboot"),
        )
    ])
    result = segment_config(config)
    assert len(result.jobs_in_segment("hourly")) == 1
    assert len(result.jobs_in_segment("daily")) == 1
    assert len(result.jobs_in_segment("weekly")) == 1
    assert len(result.jobs_in_segment("monthly")) == 1
    assert len(result.jobs_in_segment("other")) == 1


def test_integration_server_name_preserved_in_entry():
    config = Config(servers=[
        _server("prod", _job("cleanup", "0 3 * * *"))
    ])
    result = segment_config(config)
    entries = result.jobs_in_segment("daily")
    assert entries[0].server == "prod"


def test_integration_segment_counts_non_zero_for_populated_config():
    config = Config(servers=[
        _server("srv",
            _job("x", "0 6 * * *"),
            _job("y", "0 6 * * *"),
        )
    ])
    result = segment_config(config)
    counts = result.segment_counts()
    assert counts["daily"] == 2
    assert counts["hourly"] == 0
