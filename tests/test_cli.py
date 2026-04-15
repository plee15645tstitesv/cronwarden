"""Tests for the cronwarden CLI entry point."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cronwarden.cli import main


VALID_CONFIG = """
servers:
  - name: web-01
    host: 192.168.1.1

jobs:
  - name: cleanup
    server: web-01
    schedule: "0 3 * * *"
    command: /usr/bin/cleanup.sh
    description: Daily cleanup
"""

INVALID_SCHEDULE_CONFIG = """
servers:
  - name: web-01
    host: 192.168.1.1

jobs:
  - name: broken
    server: web-01
    schedule: "not-a-cron"
    command: /usr/bin/broken.sh
"""


@pytest.fixture()
def valid_config_file(tmp_path: Path) -> Path:
    p = tmp_path / "crons.yaml"
    p.write_text(VALID_CONFIG)
    return p


@pytest.fixture()
def invalid_config_file(tmp_path: Path) -> Path:
    p = tmp_path / "bad_crons.yaml"
    p.write_text(INVALID_SCHEDULE_CONFIG)
    return p


def test_cli_exits_zero_for_valid_config(valid_config_file: Path):
    runner = CliRunner()
    result = runner.invoke(main, [str(valid_config_file)])
    assert result.exit_code == 0


def test_cli_text_output_contains_server(valid_config_file: Path):
    runner = CliRunner()
    result = runner.invoke(main, [str(valid_config_file), "--format", "text"])
    assert "web-01" in result.output


def test_cli_json_output_is_valid_json(valid_config_file: Path):
    runner = CliRunner()
    result = runner.invoke(main, [str(valid_config_file), "--format", "json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert isinstance(parsed, list)


def test_cli_markdown_output_contains_header(valid_config_file: Path):
    runner = CliRunner()
    result = runner.invoke(main, [str(valid_config_file), "--format", "markdown"])
    assert "## Server:" in result.output


def test_cli_fail_fast_exits_one_on_invalid(invalid_config_file: Path):
    runner = CliRunner()
    result = runner.invoke(main, [str(invalid_config_file), "--fail-fast"])
    assert result.exit_code == 1


def test_cli_no_fail_fast_exits_zero_on_invalid(invalid_config_file: Path):
    runner = CliRunner()
    result = runner.invoke(main, [str(invalid_config_file)])
    assert result.exit_code == 0


def test_cli_missing_config_file_exits_nonzero():
    runner = CliRunner()
    result = runner.invoke(main, ["/nonexistent/path/crons.yaml"])
    assert result.exit_code != 0
