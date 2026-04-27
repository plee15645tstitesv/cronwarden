"""Tests for cronwarden/cli_mapper.py"""

import json
import pytest
from pathlib import Path
from cronwarden.cli_mapper import run_map


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
        tags:
          - backup
      - name: cleanup
        schedule: "0 3 * * 0"
        command: /usr/bin/cleanup
        tags:
          - maintenance
  - name: db
    host: db.example.com
    jobs:
      - name: dump
        schedule: "30 1 * * *"
        command: /usr/bin/pg_dump
        tags:
          - backup
"""
    p = tmp_path / "config.yaml"
    p.write_text(content)
    return str(p)


def _run(argv):
    return run_map(argv)


def test_run_map_exits_zero_for_valid_config(config_file):
    assert _run([config_file]) == 0


def test_run_map_exits_one_for_bad_config(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: cron: config")
    assert _run([str(bad)]) == 1


def test_run_map_exits_one_for_missing_file(tmp_path):
    assert _run([str(tmp_path / "missing.yaml")]) == 1


def test_run_map_json_output_is_valid(config_file, capsys):
    _run([config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "total" in data
    assert "servers" in data


def test_run_map_json_total_correct(config_file, capsys):
    _run([config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["total"] == 3


def test_run_map_text_contains_server_name(config_file, capsys):
    _run([config_file])
    out = capsys.readouterr().out
    assert "web" in out


def test_run_map_tag_filter_reduces_output(config_file, capsys):
    _run([config_file, "--tag", "backup"])
    out = capsys.readouterr().out
    assert "cleanup" not in out
    assert "backup" in out or "dump" in out


def test_run_map_verbose_shows_command(config_file, capsys):
    _run([config_file, "--verbose"])
    out = capsys.readouterr().out
    assert "/usr/bin/backup" in out or "command:" in out
