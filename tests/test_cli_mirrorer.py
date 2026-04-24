"""Tests for cronwarden.cli_mirrorer."""
import json
import pytest
from cronwarden.cli_mirrorer import run_mirror


@pytest.fixture
def config_file(tmp_path):
    content = """servers:
  - name: alpha
    jobs:
      - name: backup
        schedule: "0 2 * * *"
        command: /backup.sh
        description: Nightly backup
      - name: cleanup
        schedule: "0 3 * * 0"
        command: /cleanup.sh
  - name: beta
    jobs:
      - name: monitor
        schedule: "*/5 * * * *"
        command: /monitor.sh
"""
    f = tmp_path / "crons.yaml"
    f.write_text(content)
    return str(f)


def _run(args):
    return run_mirror(args)


def test_run_mirror_exits_zero(config_file):
    code = _run([config_file, "--from", "alpha", "--to", "beta"])
    assert code == 0


def test_run_mirror_bad_config_exits_one(tmp_path):
    missing = str(tmp_path / "nope.yaml")
    code = _run([missing, "--from", "alpha", "--to", "beta"])
    assert code == 1


def test_run_mirror_unknown_source_exits_one(config_file):
    code = _run([config_file, "--from", "unknown", "--to", "beta"])
    assert code == 1


def test_run_mirror_unknown_target_exits_one(config_file):
    code = _run([config_file, "--from", "alpha", "--to", "unknown"])
    assert code == 1


def test_run_mirror_json_output_is_valid(config_file, capsys):
    code = _run([config_file, "--from", "alpha", "--to", "beta", "--format", "json"])
    assert code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "mirrored" in data
    assert data["source_server"] == "alpha"
    assert data["target_server"] == "beta"


def test_run_mirror_text_output_contains_server_names(config_file, capsys):
    code = _run([config_file, "--from", "alpha", "--to", "beta"])
    assert code == 0
    captured = capsys.readouterr()
    assert "alpha" in captured.out
    assert "beta" in captured.out


def test_run_mirror_filter_reduces_output(config_file, capsys):
    code = _run([config_file, "--from", "alpha", "--to", "beta", "--filter", "backup", "--format", "json"])
    assert code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["total"] == 1
    assert data["mirrored"][0]["job_name"] == "backup"
