import pytest
from cronwarden.blocker import find_conflicts, BlockerResult, BlockedPair
from cronwarden.config import Config, Server, CronJob


def _make_job(name, schedule, command="/usr/bin/run", tags=None):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [])


def _make_config(servers):
    return Config(servers=servers)


def _make_server(name, jobs):
    return Server(name=name, host=f"{name}.example.com", jobs=jobs)


def test_find_conflicts_returns_blocker_result():
    config = _make_config([_make_server("web", [_make_job("a", "0 * * * *")])])
    result = find_conflicts(config)
    assert isinstance(result, BlockerResult)


def test_no_conflicts_when_all_unique_schedules():
    jobs = [
        _make_job("a", "0 * * * *"),
        _make_job("b", "30 * * * *"),
    ]
    config = _make_config([_make_server("web", jobs)])
    result = find_conflicts(config)
    assert not result.has_conflicts


def test_detects_conflict_with_identical_schedules():
    jobs = [
        _make_job("backup", "0 2 * * *"),
        _make_job("cleanup", "0 2 * * *"),
    ]
    config = _make_config([_make_server("db", jobs)])
    result = find_conflicts(config)
    assert result.has_conflicts
    assert result.total == 1


def test_conflict_pair_fields():
    jobs = [
        _make_job("job1", "*/5 * * * *"),
        _make_job("job2", "*/5 * * * *"),
    ]
    config = _make_config([_make_server("app", jobs)])
    result = find_conflicts(config)
    pair = result.pairs[0]
    assert isinstance(pair, BlockedPair)
    assert pair.server == "app"
    assert pair.job_a == "job1"
    assert pair.job_b == "job2"


def test_no_cross_server_conflicts():
    """Jobs on different servers with same schedule should not conflict."""
    j = _make_job("sync", "0 3 * * *")
    config = _make_config([
        _make_server("server1", [j]),
        _make_server("server2", [_make_job("sync", "0 3 * * *")]),
    ])
    result = find_conflicts(config)
    assert not result.has_conflicts


def test_multiple_conflicts_detected():
    jobs = [
        _make_job("a", "0 1 * * *"),
        _make_job("b", "0 1 * * *"),
        _make_job("c", "0 1 * * *"),
    ]
    config = _make_config([_make_server("web", jobs)])
    result = find_conflicts(config)
    assert result.total == 3  # (a,b), (a,c), (b,c)


def test_blocker_result_str_no_conflicts():
    config = _make_config([_make_server("web", [_make_job("a", "0 * * * *")])])
    result = find_conflicts(config)
    assert "No overlapping" in str(result)


def test_blocker_result_str_with_conflicts():
    jobs = [_make_job("a", "0 2 * * *"), _make_job("b", "0 2 * * *")]
    config = _make_config([_make_server("db", jobs)])
    result = find_conflicts(config)
    assert "db" in str(result)
    assert "a" in str(result)
    assert "b" in str(result)
