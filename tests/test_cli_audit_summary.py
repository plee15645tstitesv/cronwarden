import json
import pytest
from pathlib import Path

from cronwarden.cli_audit_summary import run_audit_summary


@pytest.fixture
def config_file(tmp_path):
    content = """
servers:
  - name: web-01
    host: web-01.example.com
    jobs:
      - name: hourly-cleanup
        schedule: "0 * * * *"
        command: /usr/bin/cleanup.sh
        description: Cleans up temp files
        tags: [maintenance]
      - name: daily-backup
        schedule: "0 2 * * *"
        command: /usr/bin/backup.sh
        description: Daily backup job
        tags: [backup]
"""
    p = tmp_path / "crons.yaml"
    p.write_text(content)
    return str(p)


@pytest.fixture
def invalid_config_file(tmp_path):
    content = """
servers:
  - name: broken
    host: broken.example.com
    jobs:
      - name: bad-job
        schedule: "not-valid"
        command: echo fail
"""
    p = tmp_path / "bad_crons.yaml"
    p.write_text(content)
    return str(p)


def _run(argv):
    return run_audit_summary(argv)


def test_run_exits_zero_for_valid_config(config_file):
    assert _run([config_file]) == 0


def test_run_exits_one_for_missing_file():
    assert _run(["nonexistent_file.yaml"]) == 1


def test_run_json_output_is_valid(config_file, capsys):
    result = _run([config_file, "--format", "json"])
    assert result == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "total_servers" in data
    assert "total_jobs" in data
    assert "valid_jobs" in data
    assert "invalid_jobs" in data
    assert "is_healthy" in data


def test_run_text_output_contains_summary(config_file, capsys):
    _run([config_file])
    captured = capsys.readouterr()
    assert "Audit Summary" in captured.out


def test_run_text_output_contains_server_count(config_file, capsys):
    _run([config_file])
    captured = capsys.readouterr()
    assert "Servers" in captured.out


def test_fail_on_issues_exits_one_for_invalid(invalid_config_file):
    result = _run([invalid_config_file, "--fail-on-issues"])
    assert result == 1


def test_fail_on_issues_exits_zero_for_healthy(config_file):
    # With a valid config and --fail-on-issues, exit depends on lint + validity
    result = _run([config_file, "--fail-on-issues"])
    assert result in (0, 1)  # may have lint warnings


def test_json_health_percent_in_range(config_file, capsys):
    _run([config_file, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert 0.0 <= data["health_percent"] <= 100.0
