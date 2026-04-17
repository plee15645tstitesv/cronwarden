import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.merger import merge_configs, MergeResult, MergeConflict


def _make_job(name, schedule="0 * * * *", command="echo hi"):
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config(server_name, jobs):
    server = Server(name=server_name, host="localhost", jobs=jobs)
    return Config(servers=[server])


def test_merge_returns_merge_result():
    c1 = _make_config("web", [_make_job("job-a")])
    result = merge_configs([c1])
    assert isinstance(result, MergeResult)


def test_merge_single_config_no_conflicts():
    c1 = _make_config("web", [_make_job("job-a"), _make_job("job-b")])
    result = merge_configs([c1])
    assert not result.has_conflicts
    assert result.total_jobs == 2


def test_merge_two_configs_different_servers():
    c1 = _make_config("web", [_make_job("job-a")])
    c2 = _make_config("db", [_make_job("job-b")])
    result = merge_configs([c1, c2])
    assert result.total_servers == 2
    assert result.total_jobs == 2
    assert not result.has_conflicts


def test_merge_same_server_different_jobs():
    c1 = _make_config("web", [_make_job("job-a")])
    c2 = _make_config("web", [_make_job("job-b")])
    result = merge_configs([c1, c2])
    assert result.total_servers == 1
    assert result.total_jobs == 2
    assert not result.has_conflicts


def test_merge_detects_duplicate_job_name():
    c1 = _make_config("web", [_make_job("job-a")])
    c2 = _make_config("web", [_make_job("job-a")])
    result = merge_configs([c1, c2])
    assert result.has_conflicts
    assert len(result.conflicts) == 1
    assert result.conflicts[0].job_name == "job-a"
    assert result.conflicts[0].server_name == "web"


def test_merge_conflict_summary_string():
    c = MergeConflict(server_name="web", job_name="backup", reason="duplicate job name across configs")
    assert "web" in c.summary()
    assert "backup" in c.summary()


def test_merge_duplicate_not_added_twice():
    c1 = _make_config("web", [_make_job("job-a")])
    c2 = _make_config("web", [_make_job("job-a")])
    result = merge_configs([c1, c2])
    assert result.total_jobs == 1


def test_merge_empty_list():
    result = merge_configs([])
    assert result.total_servers == 0
    assert result.total_jobs == 0
    assert not result.has_conflicts
