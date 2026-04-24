"""Unit tests for cronwarden.inspector."""

import pytest
from cronwarden.config import CronJob, Server
from cronwarden.inspector import inspect_job, InspectionResult


def _make_job(
    name="backup",
    schedule="0 2 * * *",
    command="/usr/bin/backup.sh",
    description="Nightly backup",
    tags=None,
):
    return CronJob(
        name=name,
        schedule=schedule,
        command=command,
        description=description,
        tags=tags or ["backup"],
    )


def _make_server(name="prod", jobs=None):
    job = jobs[0] if jobs else _make_job()
    return Server(name=name, host="localhost", jobs=jobs or [job])


def test_inspect_job_returns_inspection_result():
    job = _make_job()
    server = _make_server(jobs=[job])
    result = inspect_job(server, job)
    assert isinstance(result, InspectionResult)


def test_valid_job_is_valid():
    job = _make_job()
    server = _make_server(jobs=[job])
    result = inspect_job(server, job)
    assert result.is_valid is True
    assert result.validation_errors == []


def test_invalid_schedule_sets_is_valid_false():
    job = _make_job(schedule="not-a-cron")
    server = _make_server(jobs=[job])
    result = inspect_job(server, job)
    assert result.is_valid is False
    assert len(result.validation_errors) > 0


def test_score_is_integer():
    job = _make_job()
    server = _make_server(jobs=[job])
    result = inspect_job(server, job)
    assert isinstance(result.score, int)
    assert 0 <= result.score <= 100


def test_grade_is_string():
    job = _make_job()
    server = _make_server(jobs=[job])
    result = inspect_job(server, job)
    assert isinstance(result.grade, str)
    assert len(result.grade) > 0


def test_schedule_explanation_is_string():
    job = _make_job()
    server = _make_server(jobs=[job])
    result = inspect_job(server, job)
    assert isinstance(result.schedule_explanation, str)
    assert len(result.schedule_explanation) > 0


def test_category_is_string():
    job = _make_job()
    server = _make_server(jobs=[job])
    result = inspect_job(server, job)
    assert isinstance(result.category, str)


def test_lint_warnings_populated_for_no_description():
    job = _make_job(description=None)
    server = _make_server(jobs=[job])
    result = inspect_job(server, job)
    assert any("W001" in w for w in result.lint_warnings)


def test_summary_contains_job_name():
    job = _make_job()
    server = _make_server(jobs=[job])
    result = inspect_job(server, job)
    assert "backup" in result.summary()


def test_summary_contains_server_name():
    job = _make_job()
    server = _make_server(name="staging", jobs=[job])
    result = inspect_job(server, job)
    assert "staging" in result.summary()


def test_tags_populated():
    job = _make_job(tags=["db", "nightly"])
    server = _make_server(jobs=[job])
    result = inspect_job(server, job)
    assert "db" in result.tags
    assert "nightly" in result.tags
