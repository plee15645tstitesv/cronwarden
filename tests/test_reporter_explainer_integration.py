"""Integration tests: reporter uses explainer to enrich job reports."""

from cronwarden.config import CronJob, Server
from cronwarden.validator import ValidationResult
from cronwarden.reporter import JobReport, ServerReport, build_server_report


def _make_job(name="backup", schedule="0 2 * * *"):
    return CronJob(name=name, schedule=schedule, command="/usr/bin/backup")


def _make_server():
    return Server(name="prod-01", host="10.0.0.1", jobs=[_make_job()])


def _make_valid_result():
    return ValidationResult(valid=True, errors=[])


def _make_invalid_result():
    return ValidationResult(valid=False, errors=["Invalid schedule field"])


def test_job_report_schedule_explanation_is_string():
    job = _make_job(schedule="0 2 * * *")
    report = JobReport(job=job, result=_make_valid_result())
    assert isinstance(report.schedule_explanation, str)
    assert len(report.schedule_explanation) > 0


def test_job_report_summary_line_contains_explanation():
    job = _make_job(schedule="@daily")
    report = JobReport(job=job, result=_make_valid_result())
    assert "midnight" in report.summary_line


def test_job_report_summary_line_contains_job_name():
    job = _make_job(name="nightly-sync", schedule="0 0 * * *")
    report = JobReport(job=job, result=_make_valid_result())
    assert "nightly-sync" in report.summary_line


def test_job_report_invalid_shows_errors():
    job = _make_job()
    result = _make_invalid_result()
    report = JobReport(job=job, result=result)
    assert "Invalid schedule field" in report.summary_line
    assert "❌" in report.summary_line


def test_build_server_report_counts():
    server = _make_server()
    job1 = _make_job(name="job1")
    job2 = _make_job(name="job2")
    results = {
        job1: _make_valid_result(),
        job2: _make_invalid_result(),
    }
    report = build_server_report(server, results)
    assert report.total == 2
    assert report.passed == 1
    assert report.failed == 1
    assert report.has_failures is True


def test_build_server_report_all_valid():
    server = _make_server()
    job = _make_job()
    report = build_server_report(server, {job: _make_valid_result()})
    assert report.has_failures is False
    assert report.passed == 1
