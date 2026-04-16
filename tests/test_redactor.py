"""Tests for cronwarden.redactor."""

import pytest

from cronwarden.config import Config, Server, CronJob
from cronwarden.redactor import (
    redact_command,
    redact_config,
    RedactionResult,
    RedactedJob,
)


def _make_job(name: str, command: str) -> CronJob:
    return CronJob(name=name, schedule="@daily", command=command)


def _make_config(*pairs) -> Config:
    """pairs: (server_name, [(job_name, command), ...])"""
    servers = []
    for server_name, jobs in pairs:
        servers.append(
            Server(name=server_name, jobs=[_make_job(n, c) for n, c in jobs])
        )
    return Config(servers=servers)


# --- redact_command ---

def test_clean_command_unchanged():
    cmd = "/usr/bin/backup.sh --output /tmp/out"
    result, changed = redact_command(cmd)
    assert result == cmd
    assert changed is False


def test_password_equals_is_redacted():
    cmd = "mysql-dump --password=s3cr3t --host=db"
    result, changed = redact_command(cmd)
    assert "s3cr3t" not in result
    assert "REDACTED" in result
    assert changed is True


def test_token_flag_is_redacted():
    cmd = "deploy.sh --token mySecretToken123"
    result, changed = redact_command(cmd)
    assert "mySecretToken123" not in result
    assert "REDACTED" in result
    assert changed is True


def test_api_key_assignment_is_redacted():
    cmd = "curl -H 'api_key=abc123' https://example.com"
    result, changed = redact_command(cmd)
    assert "abc123" not in result
    assert changed is True


def test_short_password_flag_is_redacted():
    cmd = "mysql -u root -p hunter2 mydb"
    result, changed = redact_command(cmd)
    assert "hunter2" not in result
    assert changed is True


# --- redact_config ---

def test_redact_config_returns_redaction_result():
    config = _make_config(("web", [("clean", "/usr/bin/check.sh")]))
    result = redact_config(config)
    assert isinstance(result, RedactionResult)


def test_redact_config_no_sensitive_data():
    config = _make_config(("web", [("backup", "/usr/bin/backup.sh")]))
    result = redact_config(config)
    assert result.has_redactions is False
    assert result.total_redacted == 0


def test_redact_config_detects_sensitive_job():
    config = _make_config(
        ("prod", [("sync", "sync.sh --password=topsecret")])
    )
    result = redact_config(config)
    assert result.has_redactions is True
    assert result.total_redacted == 1


def test_redact_config_mixed_jobs():
    config = _make_config(
        ("prod", [
            ("safe", "/bin/safe.sh"),
            ("risky", "deploy.sh --token abc999"),
        ])
    )
    result = redact_config(config)
    assert result.total_redacted == 1
    assert len(result.jobs) == 2


def test_redacted_job_summary_includes_flag():
    job = RedactedJob(
        server="prod",
        job_name="deploy",
        original_command="deploy.sh --token secret",
        redacted_command="deploy.sh --token ***REDACTED***",
        was_redacted=True,
    )
    assert "[redacted]" in job.summary
    assert "prod/deploy" in job.summary


def test_non_redacted_job_summary_has_no_flag():
    job = RedactedJob(
        server="web",
        job_name="check",
        original_command="/bin/check.sh",
        redacted_command="/bin/check.sh",
        was_redacted=False,
    )
    assert "[redacted]" not in job.summary
