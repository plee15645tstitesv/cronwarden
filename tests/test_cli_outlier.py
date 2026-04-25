"""Tests for cronwarden.cli_outlier."""

import json
import textwrap
import pytest
from pathlib import Path
from cronwarden.cli_outlier import run_outlier


@pytest.fixture
def clean_config_file(tmp_path) -> Path:
    content = textwrap.dedent("""
        servers:
          - name: web
            jobs:
              - name: backup
                schedule: "0 2 * * *"
                command: /usr/bin/backup.sh
                description: Nightly backup
    """)
    p = tmp_path / "config.yaml"
    p.write_text(content)
    return p


@pytest.fixture
def noisy_config_file(tmp_path) -> Path:
    content = textwrap.dedent("""
        servers:
          - name: web
            jobs:
              - name: poller
                schedule: "* * * * *"
                command: /usr/bin/poll.sh
              - name: syncer
                schedule: "*/2 * * * *"
                command: /usr/bin/sync.sh
    """)
    p = tmp_path / "noisy.yaml"
    p.write_text(content)
    return p


def _run(args):
    return run_outlier(args)


def test_run_outlier_exits_zero_for_clean_config(clean_config_file):
    assert _run([str(clean_config_file)]) == 0


def test_run_outlier_exits_zero_for_noisy_without_flag(noisy_config_file):
    assert _run([str(noisy_config_file)]) == 0


def test_run_outlier_exits_one_when_fail_flag_and_outliers(noisy_config_file):
    assert _run([str(noisy_config_file), "--fail-on-outliers"]) == 1


def test_run_outlier_exits_one_for_bad_config(tmp_path):
    missing = tmp_path / "missing.yaml"
    assert _run([str(missing)]) == 1


def test_run_outlier_json_output_is_valid(noisy_config_file, capsys):
    _run([str(noisy_config_file), "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "outliers" in data
    assert "total" in data


def test_run_outlier_json_total_matches_outliers(noisy_config_file, capsys):
    _run([str(noisy_config_file), "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["total"] == len(data["outliers"])


def test_run_outlier_severity_filter_high_only(noisy_config_file, capsys):
    _run([str(noisy_config_file), "--format", "json", "--severity", "high"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    for o in data["outliers"]:
        assert o["severity"] == "high"


def test_run_outlier_text_output_no_outliers(clean_config_file, capsys):
    _run([str(clean_config_file)])
    captured = capsys.readouterr()
    assert "No outliers" in captured.out


def test_run_outlier_text_output_contains_severity(noisy_config_file, capsys):
    _run([str(noisy_config_file)])
    captured = capsys.readouterr()
    assert "HIGH" in captured.out or "MEDIUM" in captured.out
