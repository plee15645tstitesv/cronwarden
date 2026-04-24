"""Tests for cronwarden/trimmer.py"""

import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.trimmer import trim_config, TrimResult, TrimmedJob


def _make_job(name="backup", command="/usr/bin/backup.sh", schedule="0 2 * * *", tags=None):
    return CronJob(name=name, command=command, schedule=schedule, tags=tags or [])


def _make_config():
    server1 = Server(
        name="web-01",
        host="10.0.0.1",
        jobs=[
            _make_job("backup", "/usr/bin/backup.sh", tags=["backup", "nightly"]),
            _make_job("cleanup", "/usr/bin/cleanup.sh", tags=["maintenance"]),
        ],
    )
    server2 = Server(
        name="db-01",
        host="10.0.0.2",
        jobs=[
            _make_job("db-backup", "/usr/bin/db_backup.sh", tags=["backup"]),
            _make_job("report", "/usr/bin/report.sh", tags=["reporting"]),
        ],
    )
    return Config(servers=[server1, server2])


def test_trim_config_returns_trim_result():
    config = _make_config()
    result = trim_config(config)
    assert isinstance(result, TrimResult)


def test_trim_no_criteria_removes_nothing():
    config = _make_config()
    result = trim_config(config)
    assert not result.has_trimmed
    assert result.total == 0


def test_trim_by_name_removes_matching_job():
    config = _make_config()
    result = trim_config(config, names=["backup"])
    assert result.has_trimmed
    trimmed_names = [t.job_name for t in result.trimmed]
    assert "backup" in trimmed_names


def test_trim_by_name_does_not_remove_other_jobs():
    config = _make_config()
    result = trim_config(config, names=["backup"])
    all_jobs = [j.name for s in result.config.servers for j in s.jobs]
    assert "cleanup" in all_jobs
    assert "db-backup" in all_jobs


def test_trim_by_tag_removes_all_tagged_jobs():
    config = _make_config()
    result = trim_config(config, tags=["backup"])
    trimmed_names = [t.job_name for t in result.trimmed]
    assert "backup" in trimmed_names
    assert "db-backup" in trimmed_names
    assert result.total == 2


def test_trim_by_command_pattern():
    config = _make_config()
    result = trim_config(config, command_pattern="report")
    trimmed_names = [t.job_name for t in result.trimmed]
    assert "report" in trimmed_names
    assert result.total == 1


def test_trim_result_config_has_correct_server_count():
    config = _make_config()
    result = trim_config(config, names=["backup"])
    assert len(result.config.servers) == 2


def test_trimmed_job_summary_includes_server_and_name():
    t = TrimmedJob(server="web-01", job_name="backup", reason="name match: backup")
    s = t.summary()
    assert "web-01" in s
    assert "backup" in s


def test_trim_result_str_no_trimmed():
    result = TrimResult(trimmed=[], config=_make_config())
    assert "No jobs trimmed" in str(result)


def test_trim_result_str_with_trimmed():
    config = _make_config()
    result = trim_config(config, tags=["backup"])
    output = str(result)
    assert "Trimmed" in output
    assert "backup" in output
