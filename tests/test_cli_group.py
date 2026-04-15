"""Tests for cronwarden.cli_group."""

import json
import pytest
from click.testing import CliRunner
from cronwarden.cli_group import run_group


@pytest.fixture
def config_file(tmp_path):
    content = """
servers:
  - name: web-01
    host: web-01.example.com
    jobs:
      - name: backup
        schedule: "0 2 * * *"
        command: /usr/local/bin/backup.sh
        description: Nightly backup
        tags: [backup, nightly]
      - name: cleanup
        schedule: "@daily"
        command: /usr/local/bin/cleanup.sh
        tags: [maintenance]
  - name: db-01
    host: db-01.example.com
    jobs:
      - name: dump
        schedule: "0 3 * * 0"
        command: /usr/local/bin/dump.sh
        tags: [backup]
      - name: health
        schedule: "* * * * *"
        command: /usr/local/bin/health.sh
"""
    p = tmp_path / "cronwarden.yml"
    p.write_text(content)
    return str(p)


def _run(args):
    """Run run_group with given argv list and capture SystemExit."""
    try:
        run_group(args)
        return 0, ""
    except SystemExit as exc:
        return exc.code, ""


def test_group_exits_zero_for_valid_config(config_file, capsys):
    code, _ = _run([config_file, "--by", "tag"])
    assert code == 0


def test_group_text_output_contains_dimension(config_file, capsys):
    _run([config_file, "--by", "server"])
    out = capsys.readouterr().out
    assert "server" in out


def test_group_by_tag_shows_backup_group(config_file, capsys):
    _run([config_file, "--by", "tag"])
    out = capsys.readouterr().out
    assert "backup" in out


def test_group_by_server_shows_server_names(config_file, capsys):
    _run([config_file, "--by", "server"])
    out = capsys.readouterr().out
    assert "web-01" in out
    assert "db-01" in out


def test_group_by_frequency_shows_daily(config_file, capsys):
    _run([config_file, "--by", "frequency"])
    out = capsys.readouterr().out
    assert "daily" in out


def test_group_json_output_is_valid_json(config_file, capsys):
    _run([config_file, "--by", "tag", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["dimension"] == "tag"
    assert "groups" in data
    assert "total_jobs" in data


def test_group_json_contains_job_details(config_file, capsys):
    _run([config_file, "--by", "server", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    all_jobs = [j for jobs in data["groups"].values() for j in jobs]
    names = [j["job"] for j in all_jobs]
    assert "backup" in names


def test_group_exits_one_for_missing_config(tmp_path):
    code, _ = _run([str(tmp_path / "nonexistent.yml"), "--by", "tag"])
    assert code == 1
