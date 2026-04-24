"""Tests for cronwarden.cli_resolver."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from cronwarden.cli_resolver import _parse_env_args, run_resolver


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    cfg = tmp_path / "crons.yaml"
    cfg.write_text(
        textwrap.dedent(
            """
            servers:
              - name: web
                host: web.example.com
                jobs:
                  - name: deploy
                    schedule: "@daily"
                    command: /deploy.sh $ENV
                  - name: clean
                    schedule: "0 3 * * *"
                    command: /clean.sh
            """
        )
    )
    return cfg


def _run(argv):
    return run_resolver(argv)


def test_parse_env_args_valid():
    result = _parse_env_args(["ENV=production", "TOKEN=abc123"])
    assert result == {"ENV": "production", "TOKEN": "abc123"}


def test_parse_env_args_invalid_format():
    with pytest.raises(ValueError, match="Invalid env format"):
        _parse_env_args(["NOEQUALS"])


def test_run_resolver_exits_zero(config_file: Path):
    assert _run([str(config_file), "--env", "ENV=prod"]) == 0


def test_run_resolver_bad_config_exits_one(tmp_path: Path):
    assert _run([str(tmp_path / "missing.yaml")]) == 1


def test_run_resolver_invalid_env_exits_one(config_file: Path):
    assert _run([str(config_file), "--env", "BADFORMAT"]) == 1


def test_run_resolver_json_output_is_valid(config_file: Path, capsys):
    _run([str(config_file), "--format", "json", "--env", "ENV=prod"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == 2


def test_run_resolver_json_contains_resolved_command(config_file: Path, capsys):
    _run([str(config_file), "--format", "json", "--env", "ENV=staging"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    deploy = next(d for d in data if d["job"] == "deploy")
    assert deploy["resolved"] == "/deploy.sh staging"
    assert deploy["unresolved_vars"] == []


def test_run_resolver_text_output_contains_server(config_file: Path, capsys):
    _run([str(config_file)])
    captured = capsys.readouterr()
    assert "web" in captured.out


def test_run_resolver_unresolved_reported_in_json(config_file: Path, capsys):
    _run([str(config_file), "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    deploy = next(d for d in data if d["job"] == "deploy")
    assert "ENV" in deploy["unresolved_vars"]
