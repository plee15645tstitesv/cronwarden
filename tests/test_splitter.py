"""Tests for cronwarden/splitter.py"""

import pytest

from cronwarden.config import Config, Server, CronJob
from cronwarden.splitter import split_config, split_to_dict, SplitResult, SplitEntry


def _make_job(name: str, schedule: str = "0 * * * *") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=f"run_{name}.sh")


def _make_config() -> Config:
    server_a = Server(
        name="alpha",
        host="alpha.example.com",
        jobs=[_make_job("backup"), _make_job("cleanup")],
    )
    server_b = Server(
        name="beta",
        host="beta.example.com",
        jobs=[_make_job("report")],
    )
    return Config(servers=[server_a, server_b])


def test_split_config_returns_split_result():
    config = _make_config()
    result = split_config(config)
    assert isinstance(result, SplitResult)


def test_split_config_total_matches_server_count():
    config = _make_config()
    result = split_config(config)
    assert result.total == 2


def test_split_config_has_entries_true_when_populated():
    config = _make_config()
    result = split_config(config)
    assert result.has_entries is True


def test_split_config_has_entries_false_when_empty():
    result = split_config(Config(servers=[]))
    assert result.has_entries is False


def test_split_entries_are_split_entry_instances():
    config = _make_config()
    result = split_config(config)
    for entry in result.entries:
        assert isinstance(entry, SplitEntry)


def test_each_entry_has_single_server():
    config = _make_config()
    result = split_config(config)
    for entry in result.entries:
        assert len(entry.config.servers) == 1


def test_entry_server_name_matches():
    config = _make_config()
    result = split_config(config)
    names = {entry.server_name for entry in result.entries}
    assert names == {"alpha", "beta"}


def test_jobs_are_preserved_per_server():
    config = _make_config()
    result = split_config(config)
    alpha_entry = result.by_server("alpha")
    assert alpha_entry is not None
    assert len(alpha_entry.config.servers[0].jobs) == 2


def test_by_server_returns_none_for_unknown():
    config = _make_config()
    result = split_config(config)
    assert result.by_server("nonexistent") is None


def test_split_entry_summary_contains_server_name():
    config = _make_config()
    result = split_config(config)
    beta_entry = result.by_server("beta")
    assert "beta" in beta_entry.summary()


def test_split_entry_summary_contains_job_count():
    config = _make_config()
    result = split_config(config)
    alpha_entry = result.by_server("alpha")
    assert "2" in alpha_entry.summary()


def test_split_to_dict_returns_dict():
    config = _make_config()
    mapping = split_to_dict(config)
    assert isinstance(mapping, dict)


def test_split_to_dict_keys_are_server_names():
    config = _make_config()
    mapping = split_to_dict(config)
    assert set(mapping.keys()) == {"alpha", "beta"}


def test_split_to_dict_values_are_configs():
    config = _make_config()
    mapping = split_to_dict(config)
    for val in mapping.values():
        assert isinstance(val, Config)


def test_split_does_not_mutate_original_config():
    config = _make_config()
    original_server_count = len(config.servers)
    split_config(config)
    assert len(config.servers) == original_server_count
