"""Tests for cronwarden.config — config loading and validation."""

import textwrap
from pathlib import Path

import pytest

from cronwarden.config import Config, ConfigError, CronJob, Server, load_config


VALID_YAML = textwrap.dedent("""\
    servers:
      - name: web-01
        host: web-01.example.com
        user: deploy
        jobs:
          - name: daily-backup
            schedule: "0 2 * * *"
            command: /usr/local/bin/backup.sh
            description: Nightly database backup
          - name: log-rotate
            schedule: "0 0 * * 0"
            command: /usr/sbin/logrotate /etc/logrotate.conf
""")


@pytest.fixture()
def config_file(tmp_path: Path):
    """Write a valid YAML config to a temp file and return its path."""
    p = tmp_path / "cronwarden.yaml"
    p.write_text(VALID_YAML)
    return str(p)


def test_load_config_returns_config_instance(config_file):
    cfg = load_config(config_file)
    assert isinstance(cfg, Config)


def test_load_config_parses_servers(config_file):
    cfg = load_config(config_file)
    assert len(cfg.servers) == 1
    srv = cfg.servers[0]
    assert isinstance(srv, Server)
    assert srv.name == "web-01"
    assert srv.host == "web-01.example.com"
    assert srv.user == "deploy"


def test_load_config_parses_jobs(config_file):
    cfg = load_config(config_file)
    jobs = cfg.servers[0].jobs
    assert len(jobs) == 2
    backup = jobs[0]
    assert isinstance(backup, CronJob)
    assert backup.name == "daily-backup"
    assert backup.schedule == "0 2 * * *"
    assert backup.command == "/usr/local/bin/backup.sh"
    assert backup.description == "Nightly database backup"


def test_optional_description_defaults_to_none(config_file):
    cfg = load_config(config_file)
    log_rotate = cfg.servers[0].jobs[1]
    assert log_rotate.description is None


def test_missing_file_raises_config_error(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(str(tmp_path / "nonexistent.yaml"))


def test_invalid_yaml_raises_config_error(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(": invalid: yaml: [")
    with pytest.raises(ConfigError, match="Failed to parse YAML"):
        load_config(str(bad))


def test_missing_servers_key_raises_config_error(tmp_path):
    p = tmp_path / "empty.yaml"
    p.write_text("foo: bar\n")
    with pytest.raises(ConfigError, match="'servers'"):
        load_config(str(p))


def test_server_missing_required_field_raises_config_error(tmp_path):
    p = tmp_path / "bad_server.yaml"
    p.write_text("servers:\n  - name: web-01\n    host: example.com\n")
    with pytest.raises(ConfigError, match="'user'"):
        load_config(str(p))


def test_job_missing_required_field_raises_config_error(tmp_path):
    p = tmp_path / "bad_job.yaml"
    p.write_text(
        "servers:\n"
        "  - name: web-01\n"
        "    host: example.com\n"
        "    user: deploy\n"
        "    jobs:\n"
        "      - name: broken-job\n"
        "        schedule: '* * * * *'\n"
    )
    with pytest.raises(ConfigError, match="'command'"):
        load_config(str(p))
