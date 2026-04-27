"""Tests for cronwarden.cli_segmenter."""

import json
import os
import tempfile
import pytest

from cronwarden.cli_segmenter import run_segment


YAML_CONTENT = """
servers:
  - name: web
    host: web.example.com
    jobs:
      - name: daily_backup
        schedule: "0 2 * * *"
        command: /usr/bin/backup.sh
        description: Daily backup
      - name: hourly_sync
        schedule: "* * * * *"
        command: /usr/bin/sync.sh
      - name: weekly_report
        schedule: "0 9 * * 1"
        command: /usr/bin/report.sh
"""


@pytest.fixture
def config_file(tmp_path):
    f = tmp_path / "crons.yaml"
    f.write_text(YAML_CONTENT)
    return str(f)


def _run(args):
    return run_segment(args)


def test_run_segment_exits_zero_for_valid_config(config_file):
    assert _run([config_file]) == 0


def test_run_segment_exits_one_for_missing_file():
    assert _run(["/nonexistent/path.yaml"]) == 1


def test_run_segment_json_output_is_valid(config_file, capsys):
    assert _run([config_file, "--format", "json"]) == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "segments" in data
    assert "total" in data


def test_run_segment_json_contains_all_labels(config_file, capsys):
    _run([config_file, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    for label in ["hourly", "daily", "weekly", "monthly", "other"]:
        assert label in data["segments"]


def test_run_segment_text_output_contains_header(config_file, capsys):
    _run([config_file])
    captured = capsys.readouterr()
    assert "Cron Job Segments" in captured.out


def test_run_segment_filter_by_segment(config_file, capsys):
    _run([config_file, "--segment", "daily"])
    captured = capsys.readouterr()
    assert "daily_backup" in captured.out


def test_run_segment_total_in_json(config_file, capsys):
    _run([config_file, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["total"] == 3
