"""Tests for cronwarden.digester."""

import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.digester import build_digest, DigestEntry, DigestResult


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup",
              description=None, tags=None):
    return CronJob(
        name=name,
        schedule=schedule,
        command=command,
        description=description,
        tags=tags or [],
    )


def _make_config(jobs_per_server=None):
    if jobs_per_server is None:
        jobs_per_server = {"web-01": [_make_job()]}
    servers = [
        Server(name=name, jobs=jobs)
        for name, jobs in jobs_per_server.items()
    ]
    return Config(servers=servers)


def test_build_digest_returns_digest_result():
    config = _make_config()
    result = build_digest(config)
    assert isinstance(result, DigestResult)


def test_build_digest_counts_servers():
    config = _make_config({"web-01": [_make_job()], "db-01": [_make_job("db-backup")]})
    result = build_digest(config)
    assert result.total_servers == 2


def test_build_digest_counts_total_jobs():
    config = _make_config({
        "web-01": [_make_job("a"), _make_job("b")],
        "db-01": [_make_job("c")],
    })
    result = build_digest(config)
    assert result.total_jobs == 3


def test_build_digest_entries_are_digest_entry_instances():
    config = _make_config()
    result = build_digest(config)
    for entry in result.entries:
        assert isinstance(entry, DigestEntry)


def test_build_digest_entry_has_correct_server():
    config = _make_config({"web-01": [_make_job()]})
    result = build_digest(config)
    assert result.entries[0].server == "web-01"


def test_build_digest_entry_has_correct_job_name():
    config = _make_config({"web-01": [_make_job("my-job")]})
    result = build_digest(config)
    assert result.entries[0].job_name == "my-job"


def test_build_digest_valid_job_is_valid():
    config = _make_config({"web-01": [_make_job(schedule="0 * * * *")]})
    result = build_digest(config)
    assert result.entries[0].is_valid is True


def test_build_digest_invalid_job_counted():
    bad_job = _make_job(schedule="not-a-cron")
    config = _make_config({"web-01": [bad_job]})
    result = build_digest(config)
    assert result.invalid_count == 1


def test_build_digest_has_invalid_false_when_all_valid():
    config = _make_config({"web-01": [_make_job(schedule="@daily")]})
    result = build_digest(config)
    assert result.has_invalid is False


def test_build_digest_is_empty_false_when_jobs_present():
    config = _make_config()
    result = build_digest(config)
    assert result.is_empty is False


def test_build_digest_is_empty_true_when_no_jobs():
    config = Config(servers=[Server(name="empty", jobs=[])])
    result = build_digest(config)
    assert result.is_empty is True


def test_digest_entry_summary_contains_status():
    entry = DigestEntry(
        server="web-01", job_name="backup", schedule="0 2 * * *",
        command="/usr/bin/backup", runs_per_day=1.0, is_valid=True
    )
    assert "OK" in entry.summary()


def test_digest_result_str_contains_job_count():
    config = _make_config({"web-01": [_make_job(), _make_job("b")]})
    result = build_digest(config)
    assert "2" in str(result)


def test_build_digest_entry_description_preserved():
    job = _make_job(description="nightly backup")
    config = _make_config({"web-01": [job]})
    result = build_digest(config)
    assert result.entries[0].description == "nightly backup"
