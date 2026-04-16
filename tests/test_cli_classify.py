import json
import pytest
from unittest.mock import patch
from cronwarden.cli_classify import run_classify


@pytest.fixture
def config_file(tmp_path):
    content = """servers:
  - name: web
    host: web.example.com
    jobs:
      - name: backup-db
        schedule: "0 2 * * *"
        command: pg_dump mydb
        description: Backup database
      - name: purge-logs
        schedule: "0 3 * * *"
        command: /usr/bin/purge_old_logs.sh
      - name: mystery
        schedule: "*/5 * * * *"
        command: /opt/mystery.sh
"""
    f = tmp_path / "cronwarden.yaml"
    f.write_text(content)
    return str(f)


def _run(argv):
    with pytest.raises(SystemExit) as exc:
        run_classify(argv)
    return exc.value.code


def test_classify_exits_zero(config_file):
    assert _run([config_file]) == 0


def test_classify_text_contains_category(config_file, capsys):
    _run([config_file])
    out = capsys.readouterr().out
    assert "BACKUP" in out


def test_classify_text_contains_unclassified(config_file, capsys):
    _run([config_file])
    out = capsys.readouterr().out
    assert "UNCLASSIFIED" in out


def test_classify_json_output_is_valid(config_file, capsys):
    _run([config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "classified" in data
    assert "unclassified" in data
    assert "total" in data


def test_classify_json_total_correct(config_file, capsys):
    _run([config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["total"] == 3


def test_classify_bad_config_exits_one(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("not: valid: config")
    assert _run([str(f)]) == 1
