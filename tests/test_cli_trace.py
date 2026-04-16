import json
import pytest
from unittest.mock import patch
from cronwarden.cli_trace import run_trace


@pytest.fixture
def config_file(tmp_path):
    content = """
servers:
  - name: web
    host: web.example.com
    jobs:
      - name: backup
        schedule: "0 2 * * *"
        command: /usr/bin/backup.sh
        description: Daily backup
      - name: cleanup
        schedule: "30 3 * * *"
        command: rm -rf /tmp/cache
"""
    p = tmp_path / "crons.yaml"
    p.write_text(content)
    return str(p)


def _run(argv):
    with pytest.raises(SystemExit) as exc:
        run_trace(argv)
    return exc.value.code


def test_run_trace_exits_zero(config_file):
    code = _run([config_file, "backup"])
    assert code == 0


def test_run_trace_no_match_exits_zero(config_file):
    code = _run([config_file, "nonexistent_xyz"])
    assert code == 0


def test_run_trace_json_output_is_valid(config_file, capsys):
    _run([config_file, "backup", "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "matches" in data
    assert "pattern" in data
    assert data["pattern"] == "backup"


def test_run_trace_json_contains_match(config_file, capsys):
    _run([config_file, "backup", "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["total"] >= 1
    job_names = [m["job"] for m in data["matches"]]
    assert "backup" in job_names


def test_run_trace_by_schedule_field(config_file, capsys):
    _run([config_file, "0 2", "--field", "schedule", "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["field"] == "schedule"
    assert data["total"] == 1


def test_run_trace_bad_config_exits_one(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: cron: config")
    code = _run([str(bad), "backup"])
    assert code == 1


def test_run_trace_invalid_regex_exits_one(config_file):
    code = _run([config_file, "[unclosed"])
    assert code == 1
