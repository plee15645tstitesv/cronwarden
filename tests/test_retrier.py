import pytest
from cronwarden.retrier import RetryPolicy, RetryResult, RetriedJob, apply_retry_policy
from cronwarden.config import Config, Server, CronJob


def _make_job(name="backup", command="/bin/backup", schedule="0 2 * * *", tags=None):
    return CronJob(name=name, command=command, schedule=schedule, tags=tags or [])


def _make_config(*servers):
    return Config(servers=list(servers))


def _make_server(name="web", jobs=None):
    return Server(name=name, jobs=jobs or [])


def test_apply_retry_returns_retry_result():
    config = _make_config(_make_server(jobs=[_make_job()]))
    result = apply_retry_policy(config)
    assert isinstance(result, RetryResult)


def test_retry_result_has_retries_true_when_jobs():
    config = _make_config(_make_server(jobs=[_make_job()]))
    result = apply_retry_policy(config)
    assert result.has_retries() is True


def test_retry_result_has_retries_false_when_empty():
    config = _make_config(_make_server(jobs=[]))
    result = apply_retry_policy(config)
    assert result.has_retries() is False


def test_retry_result_total_counts_jobs():
    server = _make_server(jobs=[_make_job("a"), _make_job("b"), _make_job("c")])
    config = _make_config(server)
    result = apply_retry_policy(config)
    assert result.total() == 3


def test_default_policy_applied():
    config = _make_config(_make_server(jobs=[_make_job()]))
    result = apply_retry_policy(config)
    job = result.jobs[0]
    assert job.max_attempts == 3
    assert job.backoff_seconds == 60


def test_custom_policy_applied():
    policy = RetryPolicy(max_attempts=5, backoff_seconds=120)
    config = _make_config(_make_server(jobs=[_make_job()]))
    result = apply_retry_policy(config, policy=policy)
    job = result.jobs[0]
    assert job.max_attempts == 5
    assert job.backoff_seconds == 120


def test_tag_filter_excludes_unmatched():
    j1 = _make_job("a", tags=["backup"])
    j2 = _make_job("b", tags=["cleanup"])
    config = _make_config(_make_server(jobs=[j1, j2]))
    result = apply_retry_policy(config, tags=["backup"])
    assert result.total() == 1
    assert result.jobs[0].job_name == "a"


def test_tag_filter_includes_matched():
    j1 = _make_job("a", tags=["backup"])
    j2 = _make_job("b", tags=["backup", "nightly"])
    config = _make_config(_make_server(jobs=[j1, j2]))
    result = apply_retry_policy(config, tags=["backup"])
    assert result.total() == 2


def test_retried_job_summary_contains_name():
    config = _make_config(_make_server(name="prod", jobs=[_make_job("myjob")]))
    result = apply_retry_policy(config)
    assert "myjob" in result.jobs[0].summary()
    assert "prod" in result.jobs[0].summary()


def test_multiple_servers_all_included():
    s1 = _make_server("s1", jobs=[_make_job("j1")])
    s2 = _make_server("s2", jobs=[_make_job("j2")])
    config = _make_config(s1, s2)
    result = apply_retry_policy(config)
    assert result.total() == 2
    servers = {j.server for j in result.jobs}
    assert servers == {"s1", "s2"}
