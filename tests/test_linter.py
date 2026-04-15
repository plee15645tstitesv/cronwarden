"""Tests for cronwarden.linter."""

import pytest
from cronwarden.config import CronJob
from cronwarden.linter import (
    lint_job,
    lint_all,
    LintResult,
    LintWarning,
)


def _make_job(
    name="backup",
    schedule="0 2 * * *",
    command="/usr/bin/backup.sh >> /var/log/backup.log 2>&1",
    description="Nightly backup",
) -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command, description=description)


def test_lint_job_returns_lint_result():
    job = _make_job()
    result = lint_job(job)
    assert isinstance(result, LintResult)
    assert result.job_name == job.name


def test_clean_job_has_no_warnings():
    job = _make_job()
    result = lint_job(job)
    assert result.is_clean
    assert result.warnings == []


def test_w001_missing_description():
    job = _make_job(description=None)
    result = lint_job(job)
    codes = [w.code for w in result.warnings]
    assert "W001" in codes


def test_w002_sudo_command():
    job = _make_job(command="sudo /usr/bin/cleanup.sh >> /tmp/out.log 2>&1")
    result = lint_job(job)
    codes = [w.code for w in result.warnings]
    assert "W002" in codes


def test_w003_no_output_redirect():
    job = _make_job(command="/usr/bin/backup.sh")
    result = lint_job(job)
    codes = [w.code for w in result.warnings]
    assert "W003" in codes


def test_w004_every_minute_schedule():
    job = _make_job(schedule="* * * * *")
    result = lint_job(job)
    codes = [w.code for w in result.warnings]
    assert "W004" in codes


def test_w004_not_triggered_for_hourly():
    job = _make_job(schedule="0 * * * *")
    result = lint_job(job)
    codes = [w.code for w in result.warnings]
    assert "W004" not in codes


def test_multiple_warnings_accumulate():
    job = _make_job(schedule="* * * * *", command="sudo do_thing", description=None)
    result = lint_job(job)
    assert len(result.warnings) >= 3


def test_lint_warning_str():
    w = LintWarning(job_name="myjob", code="W001", message="No description.")
    assert "W001" in str(w)
    assert "myjob" in str(w)


def test_lint_all_returns_one_result_per_job():
    jobs = [_make_job(name=f"job{i}") for i in range(4)]
    results = lint_all(jobs)
    assert len(results) == 4
    assert all(isinstance(r, LintResult) for r in results)


def test_lint_all_empty_list():
    assert lint_all([]) == []
