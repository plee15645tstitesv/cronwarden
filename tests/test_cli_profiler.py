import json
import pytest
from unittest.mock import patch
from cronwarden.cli_profiler import run_profile


@pytest.fixture
def config_file(tmp_path):
    content = """
servers:
  - name: web-01
    jobs:
      - name: backup
        schedule: "0 2 * * *"
        command: /usr/bin/backup.sh
        description: Nightly backup
        tags: [backup]
      - name: cleanup
        schedule: "*/5 * * * *"
        command: rm -rf /tmp/old
"""
    f = tmp_path / "crons.yaml"
    f.write_text(content)
    return str(f)


def _run(argv):
    with pytest.raises(SystemExit) as exc:
        run_profile(argv)
    return exc.value.code


def test_run_profile_exits_zero(config_file):
    assert _run([config_file]) == 0


def test_run_profile_bad_config_exits_one(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: cron: config")
    assert _run([str(bad)]) == 1


def test_run_profile_json_output_is_valid(config_file, capsys):
    _run([config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 2


def test_run_profile_json_contains_risk(config_file, capsys):
    _run([config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert all("risk_level" in item for item in data)


def test_run_profile_risk_filter_high(config_file, capsys):
    _run([config_file, "--format", "json", "--risk", "high"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert all(item["risk_level"] == "high" for item in data)


def test_run_profile_text_contains_server(config_file, capsys):
    _run([config_file])
    out = capsys.readouterr().out
    assert "web-01" in out
