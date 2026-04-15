"""Tests for cronwarden.search module."""

import pytest

from cronwarden.config import Config, CronJob, Server
from cronwarden.search import SearchMatch, SearchResult, _job_matches, search_config


def _make_job(name="backup", command="/usr/bin/backup.sh", description=None, tags=None):
    return CronJob(
        name=name,
        schedule="0 2 * * *",
        command=command,
        description=description,
        tags=tags or [],
    )


def _make_config(*servers):
    return Config(servers=list(servers))


def _make_server(name="web-01", jobs=None):
    return Server(name=name, host="localhost", jobs=jobs or [])


# --- SearchResult ---

def test_search_result_has_matches_false_when_empty():
    result = SearchResult(query="backup")
    assert result.has_matches is False


def test_search_result_has_matches_true_when_populated():
    server = _make_server()
    job = _make_job()
    result = SearchResult(query="backup", matches=[SearchMatch(server=server, job=job, matched_fields=["name"])])
    assert result.has_matches is True


def test_search_result_total_reflects_match_count():
    server = _make_server()
    matches = [SearchMatch(server=server, job=_make_job(), matched_fields=["name"]) for _ in range(3)]
    result = SearchResult(query="x", matches=matches)
    assert result.total == 3


# --- SearchMatch ---

def test_search_match_summary_includes_server_and_job():
    server = _make_server(name="prod-01")
    job = _make_job(name="cleanup")
    match = SearchMatch(server=server, job=job, matched_fields=["name", "command"])
    summary = match.summary()
    assert "prod-01" in summary
    assert "cleanup" in summary
    assert "name" in summary
    assert "command" in summary


# --- _job_matches ---

def test_job_matches_by_name():
    job = _make_job(name="nightly-backup")
    matched, fields = _job_matches(job, "backup")
    assert matched is True
    assert "name" in fields


def test_job_matches_by_command():
    job = _make_job(command="/usr/bin/pg_dump")
    matched, fields = _job_matches(job, "pg_dump")
    assert matched is True
    assert "command" in fields


def test_job_matches_by_description():
    job = _make_job(description="Runs the weekly report generator")
    matched, fields = _job_matches(job, "weekly report")
    assert matched is True
    assert "description" in fields


def test_job_matches_by_tag():
    job = _make_job(tags=["database", "critical"])
    matched, fields = _job_matches(job, "database")
    assert matched is True
    assert "tags" in fields


def test_job_no_match_returns_false():
    job = _make_job(name="cleanup", command="/bin/clean.sh")
    matched, fields = _job_matches(job, "zzznomatch")
    assert matched is False
    assert fields == []


def test_job_match_is_case_insensitive():
    job = _make_job(name="BackupJob")
    matched, fields = _job_matches(job, "backupjob")
    assert matched is True


# --- search_config ---

def test_search_config_returns_search_result():
    config = _make_config(_make_server())
    result = search_config(config, "backup")
    assert isinstance(result, SearchResult)


def test_search_config_finds_matching_jobs():
    jobs = [_make_job(name="db-backup"), _make_job(name="log-rotate")]
    server = _make_server(jobs=jobs)
    config = _make_config(server)
    result = search_config(config, "backup")
    assert result.total == 1
    assert result.matches[0].job.name == "db-backup"


def test_search_config_no_matches():
    jobs = [_make_job(name="cleanup"), _make_job(name="report")]
    server = _make_server(jobs=jobs)
    config = _make_config(server)
    result = search_config(config, "zzznomatch")
    assert result.has_matches is False


def test_search_config_matches_across_servers():
    s1 = _make_server(name="web-01", jobs=[_make_job(name="web-backup")])
    s2 = _make_server(name="db-01", jobs=[_make_job(name="db-backup")])
    config = _make_config(s1, s2)
    result = search_config(config, "backup")
    assert result.total == 2
    server_names = {m.server.name for m in result.matches}
    assert "web-01" in server_names
    assert "db-01" in server_names
