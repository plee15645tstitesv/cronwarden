"""Tests for the reporter and auditor modules."""

import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.validator import ValidationResult
from cronwarden.reporter import JobReport, ServerReport, AuditReport, format_report
from cronwarden.auditor import audit_config, has_failures


def _make_server(host="web-01", jobs=None):
    return Server(host=host, user="deploy", jobs=jobs or [])


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup", description=None):
    return CronJob(name=name, schedule=schedule, command=command, description=description)


def _make_valid_result():
    return ValidationResult(valid=True, errors=[], warnings=[])


def _make_invalid_result(errors=None):
    return ValidationResult(valid=False, errors=errors or ["bad schedule"], warnings=[])


# --- JobReport ---

def test_job_report_status_icon_valid():
    jr = JobReport(server="web-01", job=_make_job(), result=_make_valid_result())
    assert jr.status_icon == "✓"


def test_job_report_status_icon_invalid():
    jr = JobReport(server="web-01", job=_make_job(), result=_make_invalid_result())
    assert jr.status_icon == "✗"


def test_job_report_summary_line_includes_name_and_schedule():
    job = _make_job(name="backup", schedule="0 2 * * *")
    jr = JobReport(server="web-01", job=job, result=_make_valid_result())
    line = jr.summary_line()
    assert "backup" in line
    assert "0 2 * * *" in line


def test_job_report_summary_line_includes_description():
    job = _make_job(description="nightly backup")
    jr = JobReport(server="web-01", job=job, result=_make_valid_result())
    assert "nightly backup" in jr.summary_line()


# --- ServerReport ---

def test_server_report_counts():
    sr = ServerReport(server=_make_server())
    sr.job_reports.append(JobReport("web-01", _make_job(), _make_valid_result()))
    sr.job_reports.append(JobReport("web-01", _make_job(name="x"), _make_invalid_result()))
    assert sr.total == 2
    assert sr.passed == 1
    assert sr.failed == 1


# --- AuditReport ---

def test_audit_report_aggregates_totals():
    audit = AuditReport()
    for host in ["web-01", "web-02"]:
        sr = ServerReport(server=_make_server(host=host))
        sr.job_reports.append(JobReport(host, _make_job(), _make_valid_result()))
        audit.server_reports.append(sr)
    assert audit.total_jobs == 2
    assert audit.total_passed == 2
    assert audit.total_failed == 0


# --- format_report ---

def test_format_report_contains_server_host():
    audit = AuditReport()
    sr = ServerReport(server=_make_server(host="db-01"))
    sr.job_reports.append(JobReport("db-01", _make_job(), _make_valid_result()))
    audit.server_reports.append(sr)
    output = format_report(audit)
    assert "db-01" in output


def test_format_report_shows_all_checks_passed():
    audit = AuditReport()
    sr = ServerReport(server=_make_server())
    sr.job_reports.append(JobReport("web-01", _make_job(), _make_valid_result()))
    audit.server_reports.append(sr)
    assert "ALL CHECKS PASSED" in format_report(audit)


def test_format_report_shows_some_checks_failed():
    audit = AuditReport()
    sr = ServerReport(server=_make_server())
    sr.job_reports.append(JobReport("web-01", _make_job(), _make_invalid_result()))
    audit.server_reports.append(sr)
    assert "SOME CHECKS FAILED" in format_report(audit)


# --- auditor ---

def test_audit_config_returns_audit_report():
    job = _make_job()
    server = _make_server(jobs=[job])
    config = Config(servers=[server], jobs=[])
    result = audit_config(config)
    assert isinstance(result, AuditReport)
    assert result.total_jobs == 1


def test_has_failures_false_when_all_valid():
    audit = AuditReport()
    sr = ServerReport(server=_make_server())
    sr.job_reports.append(JobReport("web-01", _make_job(), _make_valid_result()))
    audit.server_reports.append(sr)
    assert has_failures(audit) is False


def test_has_failures_true_when_invalid_job():
    audit = AuditReport()
    sr = ServerReport(server=_make_server())
    sr.job_reports.append(JobReport("web-01", _make_job(), _make_invalid_result()))
    audit.server_reports.append(sr)
    assert has_failures(audit) is True
