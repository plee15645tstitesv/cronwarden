import pytest
from cronwarden.flattener import flatten_config, FlatResult, FlatJob
from cronwarden.config import Config, Server, CronJob


def _make_job(name="job1", schedule="@daily", command="/bin/job", tags=None, description=None):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [], description=description)


def _make_config():
    s1 = Server(name="web", jobs=[_make_job("backup", tags=["backup"], description="Backs up db"), _make_job("cleanup")])
    s2 = Server(name="worker", jobs=[_make_job("sync", tags=["sync"])])
    return Config(servers=[s1, s2])


def test_flatten_config_returns_flat_result():
    result = flatten_config(_make_config())
    assert isinstance(result, FlatResult)


def test_flatten_config_total_jobs():
    result = flatten_config(_make_config())
    assert result.total == 3


def test_flatten_config_jobs_are_flat_job_instances():
    result = flatten_config(_make_config())
    for job in result.jobs:
        assert isinstance(job, FlatJob)


def test_flat_job_has_server_name():
    result = flatten_config(_make_config())
    servers = {j.server for j in result.jobs}
    assert "web" in servers
    assert "worker" in servers


def test_for_server_filters_correctly():
    result = flatten_config(_make_config())
    web_jobs = result.for_server("web")
    assert len(web_jobs) == 2
    assert all(j.server == "web" for j in web_jobs)


def test_with_tag_filters_correctly():
    result = flatten_config(_make_config())
    backup_jobs = result.with_tag("backup")
    assert len(backup_jobs) == 1
    assert backup_jobs[0].name == "backup"


def test_is_empty_false_when_jobs_present():
    result = flatten_config(_make_config())
    assert not result.is_empty


def test_is_empty_true_for_empty_config():
    result = flatten_config(Config(servers=[]))
    assert result.is_empty


def test_flat_job_summary_contains_server_and_name():
    job = FlatJob(server="web", name="backup", schedule="@daily", command="/bin/backup", description=None, tags=["backup"])
    s = job.summary()
    assert "web" in s
    assert "backup" in s


def test_flat_job_description_preserved():
    result = flatten_config(_make_config())
    backup = next(j for j in result.jobs if j.name == "backup")
    assert backup.description == "Backs up db"
