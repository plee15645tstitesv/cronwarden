"""Integration tests for resolver working with real Config objects."""

from __future__ import annotations

from cronwarden.config import Config, CronJob, Server
from cronwarden.resolver import resolve_config


def _job(name: str, command: str) -> CronJob:
    return CronJob(name=name, schedule="@hourly", command=command)


def _server(name: str, *jobs: CronJob) -> Server:
    return Server(name=name, host=f"{name}.example.com", jobs=list(jobs))


def test_integration_multi_server_all_resolved():
    config = Config(
        servers=[
            _server("web", _job("build", "/build.sh $BRANCH")),
            _server("db", _job("dump", "/dump.sh $DB_NAME")),
        ]
    )
    result = resolve_config(config, {"BRANCH": "main", "DB_NAME": "mydb"})
    assert result.total() == 2
    assert not result.has_unresolved()
    cmds = {j.job_name: j.resolved_command for j in result.jobs}
    assert cmds["build"] == "/build.sh main"
    assert cmds["dump"] == "/dump.sh mydb"


def test_integration_partial_resolution():
    config = Config(
        servers=[
            _server(
                "app",
                _job("a", "/run.sh $KNOWN"),
                _job("b", "/run.sh $UNKNOWN"),
            )
        ]
    )
    result = resolve_config(config, {"KNOWN": "value"})
    assert result.unresolved_count() == 1
    unresolved_job = next(j for j in result.jobs if j.unresolved_vars)
    assert unresolved_job.job_name == "b"


def test_integration_no_vars_no_changes():
    config = Config(
        servers=[
            _server(
                "cron",
                _job("noop", "/usr/bin/true"),
                _job("clean", "/tmp/clean.sh"),
            )
        ]
    )
    result = resolve_config(config, {"ANYTHING": "ignored"})
    assert not result.has_unresolved()
    for job in result.jobs:
        assert job.original_command == job.resolved_command
