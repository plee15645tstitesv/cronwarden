"""Tests for cronwarden.cli_watchdog."""
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from cronwarden.cli_watchdog import run_watchdog, _parse_last_seen


@pytest.fixture
def config_file(tmp_path):
    content = """
servers:
  - name: prod
    host: prod.example.com
    jobs:
      - name: backup
        schedule: "0 2 * * *"
        command: /usr/bin/backup
        description: Daily backup
"""
    f = tmp_path / "cronwarden.yml"
    f.write_text(content)
    return str(f)


def test_parse_last_seen_valid():
    result = _parse_last_seen(["prod:backup:2024-06-01T02:01:00"])
    assert ("prod", "backup") in result
    assert result[("prod", "backup")] == datetime(2024, 6, 1, 2, 1, 0)


def test_parse_last_seen_invalid_format():
    with pytest.raises(ValueError, match="Invalid last-seen"):
        _parse_last_seen(["prod:backup"])


def test_run_watchdog_exits_zero(config_file):
    with pytest.raises(SystemExit) as exc:
        run_watchdog([config_file])
    assert exc.value.code == 0


def test_run_watchdog_bad_config_exits_one(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("not: valid: config")
    with pytest.raises(SystemExit) as exc:
        run_watchdog([str(bad)])
    assert exc.value.code == 1


def test_run_watchdog_json_output_is_valid(config_file, capsys):
    with pytest.raises(SystemExit):
        run_watchdog([config_file, "--format", "json"])
    captured = capsys    data = json.loads(captured.out)
    assert "overdue" in data
    assert "total" in data


def test_run_watchdog_fail_on_overdue_exits_one(config_file):
    # Provide an old last_seen so the job appears overdue
    old_ts = "2024-01-01T02:01:00"
    with pytest.raises(SystemExit) as exc:
        run_watchdog([
            config_file,
            "--last-seen", f"prod:backup:{old_ts}",
            "--fail-on-overdue",
        ])
    assert exc.value.code == 1


def test_run_watchdog_invalid_last_seen_exits_one(config_file):
    with pytest.raises(SystemExit) as exc:
        run_watchdog([config_file, "--last-seen", "badentry"])
    assert exc.value.code == 1
