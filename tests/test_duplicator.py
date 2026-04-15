"""Tests for cronwarden.duplicator."""

import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.duplicator import find_duplicates, DuplicateResult, DuplicateGroup


def _make_job(name, schedule="0 * * * *", command="/usr/bin/backup", tags=None):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [])


def _make_config(servers):
    return Config(servers=servers)


def test_find_duplicates_returns_duplicate_result():
    config = _make_config([
        Server(name="s1", jobs=[_make_job("job1")]),
    ])
    result = find_duplicates(config)
    assert isinstance(result, DuplicateResult)


def test_no_duplicates_when_all_unique():
    config = _make_config([
        Server(name="s1", jobs=[_make_job("job1", command="/bin/a")]),
        Server(name="s2", jobs=[_make_job("job2", command="/bin/b")]),
    ])
    result = find_duplicates(config)
    assert not result.has_duplicates
    assert result.total == 0


def test_detects_duplicate_across_servers():
    job = _make_job("backup", schedule="0 2 * * *", command="/bin/backup")
    config = _make_config([
        Server(name="web", jobs=[job]),
        Server(name="db", jobs=[_make_job("backup", schedule="0 2 * * *", command="/bin/backup")]),
    ])
    result = find_duplicates(config)
    assert result.has_duplicates
    assert result.total == 1


def test_duplicate_group_contains_both_servers():
    config = _make_config([
        Server(name="web", jobs=[_make_job("j", schedule="0 1 * * *", command="/bin/x")]),
        Server(name="db", jobs=[_make_job("j", schedule="0 1 * * *", command="/bin/x")]),
    ])
    result = find_duplicates(config)
    group = result.groups[0]
    server_names = [s.name for s, _ in group.jobs]
    assert "web" in server_names
    assert "db" in server_names


def test_no_false_positive_for_same_command_different_schedule():
    config = _make_config([
        Server(name="s1", jobs=[_make_job("j", schedule="0 1 * * *", command="/bin/x")]),
        Server(name="s2", jobs=[_make_job("j", schedule="0 2 * * *", command="/bin/x")]),
    ])
    result = find_duplicates(config)
    assert not result.has_duplicates


def test_duplicate_group_summary_contains_server_names():
    config = _make_config([
        Server(name="alpha", jobs=[_make_job("j", command="/bin/run")]),
        Server(name="beta", jobs=[_make_job("j", command="/bin/run")]),
    ])
    result = find_duplicates(config)
    summary = result.groups[0].summary
    assert "alpha" in summary
    assert "beta" in summary


def test_str_no_duplicates():
    config = _make_config([Server(name="s1", jobs=[_make_job("j")])])
    result = find_duplicates(config)
    assert "No duplicate" in str(result)


def test_str_with_duplicates():
    config = _make_config([
        Server(name="s1", jobs=[_make_job("j", command="/bin/x")]),
        Server(name="s2", jobs=[_make_job("j", command="/bin/x")]),
    ])
    result = find_duplicates(config)
    assert "1 duplicate group" in str(result)


def test_multiple_duplicate_groups():
    config = _make_config([
        Server(name="s1", jobs=[
            _make_job("a", schedule="0 1 * * *", command="/bin/a"),
            _make_job("b", schedule="0 2 * * *", command="/bin/b"),
        ]),
        Server(name="s2", jobs=[
            _make_job("a", schedule="0 1 * * *", command="/bin/a"),
            _make_job("b", schedule="0 2 * * *", command="/bin/b"),
        ]),
    ])
    result = find_duplicates(config)
    assert result.total == 2
