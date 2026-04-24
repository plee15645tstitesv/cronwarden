"""Tests for cronwarden.cli_inspector."""

import json
import pytest
from argparse import Namespace
from cronwarden.cli_inspector import run_inspect, _format_text, _format_json
from cronwarden.inspector import InspectionResult


@pytest.fixture
def config_file(tmp_path):
    cfg = tmp_path / "crons.yaml"
    cfg.write_text(
        "servers:\n"
        "  - name: web\n"
        "    host: web.example.com\n"
        "    jobs:\n"
        "      - name: cleanup\n"
        "        schedule: '0 3 * * *'\n"
        "        command: /usr/bin/cleanup.sh\n"
        "        description: Daily cleanup\n"
        "        tags: [maintenance]\n"
    )
    return str(cfg)


def _run(config, server, job, fmt="text"):
    return Namespace(config=config, server=server, job=job, format=fmt)


def test_run_inspect_exits_zero_for_valid_job(config_file):
    args = _run(config_file, "web", "cleanup")
    assert run_inspect(args) == 0


def test_run_inspect_exits_one_for_missing_job(config_file):
    args = _run(config_file, "web", "nonexistent")
    assert run_inspect(args) == 1


def test_run_inspect_exits_one_for_missing_server(config_file):
    args = _run(config_file, "missing-server", "cleanup")
    assert run_inspect(args) == 1


def test_run_inspect_exits_one_for_bad_config(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: cron: config\n")
    args = _run(str(bad), "web", "cleanup")
    assert run_inspect(args) == 1


def test_run_inspect_json_output_is_valid(config_file, capsys):
    args = _run(config_file, "web", "cleanup", fmt="json")
    run_inspect(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "job_name" in data
    assert data["job_name"] == "cleanup"


def test_format_text_contains_schedule():
    r = InspectionResult(
        server_name="s", job_name="j", schedule="@daily",
        command="cmd", description="desc", tags=[],
        is_valid=True, validation_errors=[], lint_warnings=[],
        score=90, grade="A", schedule_explanation="Once a day",
        category="maintenance",
    )
    out = _format_text(r)
    assert "@daily" in out
    assert "Once a day" in out


def test_format_json_round_trips():
    r = InspectionResult(
        server_name="s", job_name="j", schedule="* * * * *",
        command="cmd", description=None, tags=["x"],
        is_valid=True, validation_errors=[], lint_warnings=[],
        score=70, grade="B", schedule_explanation="Every minute",
        category="other",
    )
    data = json.loads(_format_json(r))
    assert data["score"] == 70
    assert data["tags"] == ["x"]
