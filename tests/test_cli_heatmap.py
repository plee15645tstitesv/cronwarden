"""Tests for cronwarden.cli_heatmap."""

import json
import textwrap
from pathlib import Path

import pytest

from cronwarden.cli_heatmap import run_heatmap


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""
        servers:
          - name: prod
            host: prod.example.com
            jobs:
              - name: backup
                schedule: "0 2 * * *"
                command: /usr/bin/backup.sh
                description: Nightly backup
              - name: cleanup
                schedule: "30 4 * * 1"
                command: /usr/bin/cleanup.sh
    """)
    p = tmp_path / "crons.yaml"
    p.write_text(content)
    return p


def _run(args):
    return run_heatmap(args)


def test_run_heatmap_exits_zero(config_file):
    assert _run([str(config_file)]) == 0


def test_run_heatmap_bad_config_exits_one(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: cron: config")
    assert _run([str(bad)]) == 1


def test_run_heatmap_missing_file_exits_one(tmp_path):
    assert _run([str(tmp_path / "missing.yaml")]) == 1


def test_run_heatmap_json_output_is_valid(config_file, capsys):
    _run([str(config_file), "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "total_jobs" in data
    assert "cells" in data


def test_run_heatmap_json_total_jobs(config_file, capsys):
    _run([str(config_file), "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["total_jobs"] == 2


def test_run_heatmap_text_contains_heatmap_header(config_file, capsys):
    _run([str(config_file)])
    out = capsys.readouterr().out
    assert "Heatmap" in out


def test_run_heatmap_text_contains_peak(config_file, capsys):
    _run([str(config_file)])
    out = capsys.readouterr().out
    assert "Peak" in out
