"""Tests for cronwarden.rotator."""
import pytest
from cronwarden.rotator import (
    RotationSuggestion,
    RotationResult,
    rotate_config,
    _parse_minute,
    _suggest_offset,
)
from cronwarden.config import Config, Server, CronJob


def _make_job(name: str, schedule: str, command: str = "echo test") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


# --- unit: _parse_minute ---

def test_parse_minute_fixed():
    assert _parse_minute("0 * * * *") == 0


def test_parse_minute_non_zero():
    assert _parse_minute("30 2 * * *") == 30


def test_parse_minute_wildcard_returns_minus_one():
    assert _parse_minute("* * * * *") == -1


def test_parse_minute_step_returns_minus_one():
    assert _parse_minute("*/5 * * * *") == -1


def test_parse_minute_invalid_schedule_returns_minus_one():
    assert _parse_minute("@daily") == -1


# --- unit: _suggest_offset ---

def test_suggest_offset_single_job_unchanged():
    assert _suggest_offset(0, 0, 1) == 0


def test_suggest_offset_spreads_jobs():
    offsets = [_suggest_offset(0, i, 4) for i in range(4)]
    assert len(set(offsets)) == 4


# --- RotationResult ---

def test_rotation_result_empty_has_no_suggestions():
    result = RotationResult()
    assert not result.has_suggestions
    assert result.total == 0


def test_rotation_result_str_empty():
    result = RotationResult()
    assert "No rotation" in str(result)


def test_rotation_result_with_suggestions():
    s = RotationSuggestion(
        server="web", job_name="backup",
        current_schedule="0 * * * *",
        suggested_schedule="15 * * * *",
        reason="2 jobs share minute :00",
    )
    result = RotationResult(suggestions=[s])
    assert result.has_suggestions
    assert result.total == 1
    assert "backup" in str(result)


# --- rotate_config ---

def test_no_suggestions_when_jobs_have_unique_minutes():
    server = Server(
        name="prod",
        host="prod.example.com",
        jobs=[
            _make_job("job_a", "0 1 * * *"),
            _make_job("job_b", "0 2 * * *"),
        ],
    )
    result = rotate_config(_make_config(server))
    assert not result.has_suggestions


def test_suggestions_when_two_jobs_share_minute():
    server = Server(
        name="prod",
        host="prod.example.com",
        jobs=[
            _make_job("job_a", "0 1 * * *"),
            _make_job("job_b", "0 2 * * *"),
            _make_job("job_c", "0 1 * * *"),
        ],
    )
    result = rotate_config(_make_config(server))
    assert result.has_suggestions
    assert result.total >= 1


def test_suggestion_changes_minute_field():
    server = Server(
        name="prod",
        host="prod.example.com",
        jobs=[
            _make_job("job_a", "0 3 * * *"),
            _make_job("job_b", "0 3 * * *"),
        ],
    )
    result = rotate_config(_make_config(server))
    assert result.has_suggestions
    suggestion = result.suggestions[0]
    parts = suggestion.suggested_schedule.split()
    assert parts[0] != "0"
    # non-minute fields preserved
    assert parts[1:] == ["3", "*", "*", "*"]


def test_wildcard_schedules_not_flagged():
    server = Server(
        name="prod",
        host="prod.example.com",
        jobs=[
            _make_job("job_a", "*/5 * * * *"),
            _make_job("job_b", "*/5 * * * *"),
        ],
    )
    result = rotate_config(_make_config(server))
    assert not result.has_suggestions


def test_rotation_suggestion_summary_contains_job_name():
    s = RotationSuggestion(
        server="web", job_name="cleanup",
        current_schedule="0 * * * *",
        suggested_schedule="20 * * * *",
        reason="3 jobs share minute :00",
    )
    assert "cleanup" in s.summary()
    assert "->" in s.summary()
