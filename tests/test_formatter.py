"""Tests for cronwarden.formatter."""

from __future__ import annotations

import json

import pytest

from cronwarden.formatter import render, format_text, format_json, format_markdown
from cronwarden.reporter import JobReport, ServerReport
from cronwarden.validator import ValidationResult


def _valid_result() -> ValidationResult:
    return ValidationResult(valid=True, issues=[])


def _invalid_result() -> ValidationResult:
    return ValidationResult(valid=False, issues=["Invalid schedule", "Missing command"])


def _make_server(name: str = "web-01", valid: bool = True) -> ServerReport:
    result = _valid_result() if valid else _invalid_result()
    jobs = [
        JobReport(
            job_name="backup",
            schedule="0 2 * * *",
            result=result,
            description="Nightly backup",
        )
    ]
    return ServerReport(server_name=name, job_reports=jobs)


# --- text format ---

def test_format_text_contains_server_name():
    report = _make_server("web-01")
    output = format_text([report])
    assert "web-01" in output


def test_format_text_contains_job_name():
    report = _make_server()
    output = format_text([report])
    assert "backup" in output


def test_format_text_shows_issues_for_invalid_job():
    report = _make_server(valid=False)
    output = format_text([report])
    assert "Invalid schedule" in output
    assert "Missing command" in output


def test_format_text_shows_total():
    report = _make_server()
    output = format_text([report])
    assert "Total: 1 job(s)" in output


# --- json format ---

def test_format_json_is_valid_json():
    report = _make_server()
    output = format_json([report])
    parsed = json.loads(output)
    assert isinstance(parsed, list)


def test_format_json_structure():
    report = _make_server("db-01")
    parsed = json.loads(format_json([report]))
    assert parsed[0]["server"] == "db-01"
    assert parsed[0]["total_jobs"] == 1
    assert parsed[0]["jobs"][0]["name"] == "backup"
    assert parsed[0]["jobs"][0]["valid"] is True


def test_format_json_invalid_job_has_issues():
    report = _make_server(valid=False)
    parsed = json.loads(format_json([report]))
    assert len(parsed[0]["jobs"][0]["issues"]) == 2


# --- markdown format ---

def test_format_markdown_contains_header():
    report = _make_server("cache-01")
    output = format_markdown([report])
    assert "## Server: `cache-01`" in output


def test_format_markdown_contains_table_header():
    output = format_markdown([_make_server()])
    assert "|" in output


def test_format_markdown_contains_job_row():
    output = format_markdown([_make_server()])
    assert "`backup`" in output


# --- render dispatcher ---

def test_render_dispatches_text():
    output = render([_make_server()], fmt="text")
    assert "web-01" in output


def test_render_dispatches_json():
    output = render([_make_server()], fmt="json")
    json.loads(output)  # should not raise


def test_render_dispatches_markdown():
    output = render([_make_server()], fmt="markdown")
    assert "##" in output


def test_render_raises_on_unknown_format():
    with pytest.raises(ValueError, match="Unknown format"):
        render([_make_server()], fmt="csv")
