import json
import pytest
from unittest.mock import patch
from cronwarden.cli_blocker import run_blocker


@pytest.fixture
def config_file(tmp_path):
    content = """
servers:
  - name: web
    host: web.example.com
    jobs:
      - name: backup
        schedule: "0 2 * * *"
        command: /usr/bin/backup
        description: Nightly backup
      - name: cleanup
        schedule: "0 3 * * *"
        command: /usr/bin/cleanup
        description: Cleanup old files
"""
    f = tmp_path / "cronwarden.yaml"
    f.write_text(content)
    return str(f)


@pytest.fixture
def conflict_config_file(tmp_path):
    content = """
servers:
  - name: db
    host: db.example.com
    jobs:
      - name: job_a
        schedule: "0 2 * * *"
        command: /usr/bin/job_a
      - name: job_b
        schedule: "0 2 * * *"
        command: /usr/bin/job_b
"""
    f = tmp_path / "conflict.yaml"
    f.write_text(content)
    return str(f)


def _run(argv):
    with pytest.raises(SystemExit) as exc:
        run_blocker(argv)
    return exc.value.code


def test_run_blocker_exits_zero_no_conflicts(config_file):
    assert _run([config_file]) == 0


def test_run_blocker_exits_zero_with_conflicts_no_flag(conflict_config_file):
    assert _run([conflict_config_file]) == 0


def test_run_blocker_exits_one_with_fail_flag(conflict_config_file):
    assert _run([conflict_config_file, "--fail-on-conflict"]) == 1


def test_run_blocker_json_output_is_valid(config_file, capsys):
    _run([config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "has_conflicts" in data
    assert "pairs" in data


def test_run_blocker_json_conflict_output(conflict_config_file, capsys):
    _run([conflict_config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["has_conflicts"] is True
    assert data["total"] == 1


def test_run_blocker_bad_config_exits_one(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: cron: config")
    assert _run([str(bad)]) == 1
