"""Tests for cronwarden.deduplicator."""
import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.deduplicator import (
    deduplicate_config,
    DeduplicationResult,
    DeduplicatedJob,
    _job_key,
)


def _make_job(name: str, schedule: str = "0 * * * *", command: str = "/bin/true") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def test_deduplicate_returns_deduplication_result():
    cfg = _make_config(Server(name="web", jobs=[_make_job("job1")]))
    result = deduplicate_config(cfg)
    assert isinstance(result, DeduplicationResult)


def test_no_duplicates_when_all_unique():
    jobs = [
        _make_job("backup", "0 2 * * *", "/backup.sh"),
        _make_job("cleanup", "0 3 * * *", "/clean.sh"),
    ]
    cfg = _make_config(Server(name="web", jobs=jobs))
    result = deduplicate_config(cfg)
    assert not result.has_duplicates
    assert result.total == 0


def test_detects_duplicate_same_server():
    job_a = _make_job("job_a", "0 1 * * *", "/run.sh")
    job_b = _make_job("job_b", "0 1 * * *", "/run.sh")
    cfg = _make_config(Server(name="web", jobs=[job_a, job_b]))
    result = deduplicate_config(cfg)
    assert result.has_duplicates
    assert result.total == 1
    assert result.duplicates[0].job.name == "job_b"
    assert result.duplicates[0].duplicate_of == "web:job_a"


def test_detects_duplicate_across_servers():
    job_a = _make_job("nightly", "0 0 * * *", "/nightly.sh")
    job_b = _make_job("nightly_copy", "0 0 * * *", "/nightly.sh")
    cfg = _make_config(
        Server(name="server1", jobs=[job_a]),
        Server(name="server2", jobs=[job_b]),
    )
    result = deduplicate_config(cfg)
    assert result.has_duplicates
    assert result.duplicates[0].server_name == "server2"
    assert result.duplicates[0].duplicate_of == "server1:nightly"


def test_total_jobs_scanned():
    jobs = [_make_job(f"job{i}", f"{i} * * * *", f"/cmd{i}.sh") for i in range(5)]
    cfg = _make_config(Server(name="web", jobs=jobs))
    result = deduplicate_config(cfg)
    assert result.total_jobs_scanned == 5


def test_is_empty_false_when_jobs_exist():
    cfg = _make_config(Server(name="web", jobs=[_make_job("j1")]))
    result = deduplicate_config(cfg)
    assert not result.is_empty()


def test_is_empty_true_when_no_jobs():
    cfg = _make_config(Server(name="web", jobs=[]))
    result = deduplicate_config(cfg)
    assert result.is_empty()


def test_duplicate_summary_string():
    job_a = _make_job("alpha", "*/5 * * * *", "/poll.sh")
    job_b = _make_job("beta", "*/5 * * * *", "/poll.sh")
    cfg = _make_config(Server(name="prod", jobs=[job_a, job_b]))
    result = deduplicate_config(cfg)
    summary = result.duplicates[0].summary()
    assert "beta" in summary
    assert "prod:alpha" in summary


def test_job_key_uses_schedule_and_command():
    job = _make_job("x", " 0 2 * * * ", " /foo.sh ")
    key = _job_key(job)
    assert "0 2 * * *" in key
    assert "/foo.sh" in key


def test_multiple_duplicates_counted():
    base = _make_job("orig", "0 6 * * *", "/morning.sh")
    dup1 = _make_job("dup1", "0 6 * * *", "/morning.sh")
    dup2 = _make_job("dup2", "0 6 * * *", "/morning.sh")
    cfg = _make_config(Server(name="web", jobs=[base, dup1, dup2]))
    result = deduplicate_config(cfg)
    assert result.total == 2
