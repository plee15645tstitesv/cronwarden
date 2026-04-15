"""Tests for cronwarden.cli_score."""
import json
import pytest
from unittest.mock import MagicMock
from cronwarden.cli_score import run_score, _format_text, _format_json
from cronwarden.scorer import JobScore, ScoreResult


@pytest.fixture
def config_file(tmp_path):
    cfg = tmp_path / "cronwarden.yaml"
    cfg.write_text(
        "servers:\n"
        "  - name: web01\n"
        "    jobs:\n"
        "      - name: backup\n"
        "        schedule: '0 2 * * *'\n"
        "        command: /usr/bin/backup\n"
        "        description: Nightly backup\n"
        "        tags: [backup]\n"
    )
    return str(cfg)


def _args(config, fmt="text"):
    a = MagicMock()
    a.config = config
    a.format = fmt
    return a


def test_run_score_exits_zero_for_healthy_config(config_file):
    code = run_score(_args(config_file))
    assert code == 0


def test_run_score_bad_config_exits_one(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: yaml: [")
    code = run_score(_args(str(bad)))
    assert code == 1


def test_run_score_json_output_is_valid(config_file, capsys):
    run_score(_args(config_file, fmt="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "average_score" in data
    assert "scores" in data
    assert isinstance(data["scores"], list)


def test_run_score_text_output_contains_server(config_file, capsys):
    run_score(_args(config_file, fmt="text"))
    out = capsys.readouterr().out
    assert "web01" in out


def test_format_text_shows_average():
    scores = [JobScore(server_name="s", job_name="j", score=85)]
    result = ScoreResult(scores=scores)
    text = _format_text(result)
    assert "85" in text
    assert "Average score" in text


def test_format_json_contains_grade():
    scores = [JobScore(server_name="s", job_name="j", score=92)]
    result = ScoreResult(scores=scores)
    data = json.loads(_format_json(result))
    assert data["scores"][0]["grade"] == "A"


def test_format_text_shows_reasons():
    scores = [JobScore(server_name="s", job_name="j", score=70, reasons=["no tags assigned"])]
    result = ScoreResult(scores=scores)
    text = _format_text(result)
    assert "no tags assigned" in text
