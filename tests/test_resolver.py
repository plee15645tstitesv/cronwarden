"""Tests for cronwarden.resolver."""

from __future__ import annotations

import pytest

from cronwarden.config import Config, CronJob, Server
from cronwarden.resolver import (
    ResolveResult,
    ResolvedJob,
    _find_vars,
    _resolve_command,
    resolve_config,
)


def _make_job(name: str, command: str) -> CronJob:
    return CronJob(name=name, schedule="@daily", command=command)


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def test_find_vars_dollar_brace():
    assert _find_vars("echo ${HOME}") == ["HOME"]


def test_find_vars_plain_dollar():
    assert _find_vars("echo $USER") == ["USER"]


def test_find_vars_multiple():
    result = _find_vars("/opt/run.sh $ENV ${TOKEN}")
    assert "ENV" in result
    assert "TOKEN" in result


def test_find_vars_none():
    assert _find_vars("/usr/bin/backup.sh") == []


def test_resolve_command_substitutes_value():
    resolved, missing = _resolve_command("/bin/run $ENV", {"ENV": "production"})
    assert resolved == "/bin/run production"
    assert missing == []


def test_resolve_command_brace_syntax():
    resolved, missing = _resolve_command("echo ${MSG}", {"MSG": "hello"})
    assert resolved == "echo hello"
    assert missing == []


def test_resolve_command_missing_var():
    resolved, missing = _resolve_command("/bin/run $SECRET", {})
    assert "SECRET" in missing
    assert "$SECRET" in resolved


def test_resolve_config_returns_resolve_result():
    server = Server(
        name="web",
        host="web.example.com",
        jobs=[_make_job("deploy", "/deploy.sh $ENV")],
    )
    config = _make_config(server)
    result = resolve_config(config, {"ENV": "prod"})
    assert isinstance(result, ResolveResult)


def test_resolve_config_total_matches_jobs():
    server = Server(
        name="web",
        host="web.example.com",
        jobs=[
            _make_job("a", "/a.sh"),
            _make_job("b", "/b.sh $X"),
        ],
    )
    config = _make_config(server)
    result = resolve_config(config, {"X": "1"})
    assert result.total() == 2


def test_resolve_config_has_unresolved_when_missing_env():
    server = Server(
        name="db",
        host="db.example.com",
        jobs=[_make_job("backup", "/backup.sh $DB_PASS")],
    )
    config = _make_config(server)
    result = resolve_config(config, {})
    assert result.has_unresolved()
    assert result.unresolved_count() == 1


def test_resolve_config_no_unresolved_when_all_provided():
    server = Server(
        name="db",
        host="db.example.com",
        jobs=[_make_job("backup", "/backup.sh $DB_PASS")],
    )
    config = _make_config(server)
    result = resolve_config(config, {"DB_PASS": "secret"})
    assert not result.has_unresolved()


def test_resolve_config_no_vars_unchanged():
    server = Server(
        name="app",
        host="app.example.com",
        jobs=[_make_job("clean", "/usr/bin/clean.sh")],
    )
    config = _make_config(server)
    result = resolve_config(config, {})
    assert result.jobs[0].resolved_command == "/usr/bin/clean.sh"
    assert result.jobs[0].unresolved_vars == []


def test_resolved_job_summary_fully_resolved():
    job = ResolvedJob(
        server="web",
        job_name="deploy",
        original_command="/deploy.sh prod",
        resolved_command="/deploy.sh prod",
        unresolved_vars=[],
    )
    assert "fully resolved" in job.summary()


def test_resolved_job_summary_unresolved():
    job = ResolvedJob(
        server="web",
        job_name="deploy",
        original_command="/deploy.sh $ENV",
        resolved_command="/deploy.sh $ENV",
        unresolved_vars=["ENV"],
    )
    assert "unresolved" in job.summary()
    assert "ENV" in job.summary()
