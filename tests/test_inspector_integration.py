"""Integration tests: inspect_job wired to a real config file."""

import pytest
from cronwarden.config import load_config
from cronwarden.inspector import inspect_job


@pytest.fixture
def config_file(tmp_path):
    cfg = tmp_path / "crons.yaml"
    cfg.write_text(
        "servers:\n"
        "  - name: prod\n"
        "    host: prod.example.com\n"
        "    jobs:\n"
        "      - name: db-backup\n"
        "        schedule: '0 1 * * *'\n"
        "        command: /usr/bin/pg_dump mydb\n"
        "        description: Postgres nightly backup\n"
        "        tags: [backup, database]\n"
        "      - name: log-rotate\n"
        "        schedule: '0 0 * * 0'\n"
        "        command: sudo logrotate /etc/logrotate.conf\n"
        "        tags: [maintenance]\n"
    )
    return str(cfg)


def test_integration_valid_job_is_inspected(config_file):
    config = load_config(config_file)
    server = config.servers[0]
    job = server.jobs[0]
    result = inspect_job(server, job)
    assert result.is_valid is True
    assert result.job_name == "db-backup"
    assert result.server_name == "prod"


def test_integration_backup_job_category(config_file):
    config = load_config(config_file)
    server = config.servers[0]
    job = server.jobs[0]
    result = inspect_job(server, job)
    assert result.category == "backup"


def test_integration_sudo_job_has_lint_warning(config_file):
    config = load_config(config_file)
    server = config.servers[0]
    sudo_job = server.jobs[1]
    result = inspect_job(server, sudo_job)
    assert any("W002" in w for w in result.lint_warnings)


def test_integration_missing_description_reduces_score(config_file):
    config = load_config(config_file)
    server = config.servers[0]
    with_desc = server.jobs[0]
    without_desc = server.jobs[1]
    r1 = inspect_job(server, with_desc)
    r2 = inspect_job(server, without_desc)
    assert r1.score >= r2.score


def test_integration_schedule_explanation_non_empty(config_file):
    config = load_config(config_file)
    server = config.servers[0]
    for job in server.jobs:
        result = inspect_job(server, job)
        assert result.schedule_explanation.strip() != ""
