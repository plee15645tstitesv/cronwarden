"""Integration tests for normalizer: alias round-trip and multi-server."""

import pytest
from cronwarden.normalizer import normalize_config, _normalize_schedule
from cronwarden.config import Config, Server, CronJob


def _job(name, schedule):
    return CronJob(name=name, schedule=schedule, command=f"cmd_{name}")


def _server(name, jobs):
    return Server(name=name, jobs=jobs)


def test_all_aliases_are_recognized():
    aliases = ["@yearly", "@annually", "@monthly", "@weekly", "@daily", "@midnight", "@hourly"]
    for alias in aliases:
        _, changed = _normalize_schedule(alias)
        assert changed is True, f"Expected {alias!r} to be normalized"


def test_multi_server_normalization_counts_all_jobs():
    config = Config(servers=[
        _server("web", [_job("j1", "@daily"), _job("j2", "0 0 * * *")]),
        _server("db", [_job("j3", "@hourly"), _job("j4", "*/5 * * * *")]),
    ])
    result = normalize_config(config)
    assert result.total == 4
    assert result.total_changed == 2


def test_normalization_preserves_server_attribution():
    config = Config(servers=[
        _server("alpha", [_job("backup", "@daily")]),
        _server("beta", [_job("sync", "@hourly")]),
    ])
    result = normalize_config(config)
    servers_in_result = {j.server for j in result.jobs}
    assert "alpha" in servers_in_result
    assert "beta" in servers_in_result


def test_whitespace_normalization_detected_as_change():
    _, changed = _normalize_schedule("0  0  *  *  *")
    assert changed is True


def test_already_normalized_five_field_not_changed():
    schedule, changed = _normalize_schedule("*/15 * * * *")
    assert changed is False
    assert schedule == "*/15 * * * *"
