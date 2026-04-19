import pytest
from cronwarden.retrier import apply_retry_policy, RetryPolicy
from cronwarden.config import Config, Server, CronJob


def _job(name, command, schedule, tags=None):
    return CronJob(name=name, command=command, schedule=schedule, tags=tags or [])


def _server(name, jobs):
    return Server(name=name, jobs=jobs)


def test_integration_all_jobs_get_policy():
    config = Config(servers=[
        _server("web", [_job("a", "/cmd", "* * * * *"), _job("b", "/cmd2", "0 * * * *")]),
        _server("db", [_job("c", "/cmd3", "0 0 * * *")]),
    ])
    result = apply_retry_policy(config, RetryPolicy(max_attempts=2, backoff_seconds=30))
    assert result.total() == 3
    assert all(j.max_attempts == 2 for j in result.jobs)
    assert all(j.backoff_seconds == 30 for j in result.jobs)


def test_integration_tag_filter_across_servers():
    config = Config(servers=[
        _server("web", [
            _job("a", "/cmd", "* * * * *", tags=["backup"]),
            _job("b", "/cmd2", "0 * * * *", tags=["cleanup"]),
        ]),
        _server("db", [
            _job("c", "/cmd3", "0 0 * * *", tags=["backup"]),
        ]),
    ])
    result = apply_retry_policy(config, tags=["backup"])
    assert result.total() == 2
    names = {j.job_name for j in result.jobs}
    assert names == {"a", "c"}


def test_integration_no_jobs_returns_empty():
    config = Config(servers=[_server("empty", [])])
    result = apply_retry_policy(config)
    assert result.has_retries() is False
    assert result.total() == 0
