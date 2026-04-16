import json
import pytest
from unittest.mock import patch
from cronwarden.cli_annotate import run_annotate, _parse_notes


CONFIG_YAML = """
servers:
  - name: web-01
    host: web-01.example.com
    jobs:
      - name: backup
        schedule: "0 2 * * *"
        command: /usr/bin/backup
        description: Nightly backup
      - name: cleanup
        schedule: "0 3 * * *"
        command: /usr/bin/clean
"""


@pytest.fixture
def config_file(tmp_path):
    f = tmp_path / "crons.yaml"
    f.write_text(CONFIG_YAML)
    return str(f)


def _run(argv):
    with pytest.raises(SystemExit) as exc:
        run_annotate(argv)
    return exc.value.code


def test_parse_notes_valid():
    notes = _parse_notes(["web-01:backup:important job"])
    assert notes == {"web-01": {"backup": "important job"}}


def test_parse_notes_invalid_format():
    with pytest.raises(ValueError):
        _parse_notes(["bad-format"])


def test_run_annotate_exits_zero(config_file):
    code = _run([config_file])
    assert code == 0


def test_run_annotate_no_notes_prints_no_annotations(config_file, capsys):
    _run([config_file])
    out = capsys.readouterr().out
    assert "No annotations" in out


def test_run_annotate_with_note_prints_summary(config_file, capsys):
    _run([config_file, "--note", "web-01:backup:critical"])
    out = capsys.readouterr().out
    assert "backup" in out
    assert "critical" in out


def test_run_annotate_json_output_is_valid(config_file, capsys):
    _run([config_file, "--note", "web-01:backup:check", "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["job"] == "backup"


def test_run_annotate_bad_config_exits_one(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: cron: config")
    code = _run([str(bad)])
    assert code == 1


def test_run_annotate_invalid_note_format_exits_one(config_file):
    code = _run([config_file, "--note", "badformat"])
    assert code == 1
