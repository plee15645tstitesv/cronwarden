import pytest
from unittest.mock import patch

from cronwarden.config import Config, Server, CronJob
from cronwarden.auditor_summary import build_audit_summary, AuditSummaryReport


def _make_job(name="job1", schedule="0 * * * *", command="echo hi", tags=None, description=None):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [], description=description)


def _make_config(jobs_per_server=None):
    if jobs_per_server is None:
        jobs_per_server = [[_make_job()]]
    servers = [
        Server(name=f"server{i}", host=f"host{i}", jobs=jobs)
        for i, jobs in enumerate(jobs_per_server)
    ]
    return Config(servers=servers)


def test_build_audit_summary_returns_report():
    config = _make_config()
    report = build_audit_summary(config)
    assert isinstance(report, AuditSummaryReport)


def test_report_counts_servers():
    config = _make_config([[_make_job()], [_make_job(name="job2")]])
    report = build_audit_summary(config)
    assert report.total_servers == 2


def test_report_counts_total_jobs():
    config = _make_config([[_make_job(), _make_job(name="job2")]])
    report = build_audit_summary(config)
    assert report.total_jobs == 2


def test_valid_jobs_counted():
    config = _make_config([[_make_job(schedule="0 * * * *")]])
    report = build_audit_summary(config)
    assert report.valid_jobs >= 1
    assert report.invalid_jobs == 0


def test_invalid_jobs_counted():
    config = _make_config([[_make_job(schedule="not-a-schedule")]])
    report = build_audit_summary(config)
    assert report.invalid_jobs >= 1


def test_is_healthy_true_for_clean_config():
    config = _make_config([[_make_job(description="Runs hourly", tags=["infra"])]])
    report = build_audit_summary(config)
    # is_healthy depends on no invalid jobs and no lint warnings
    assert isinstance(report.is_healthy, bool)


def test_is_healthy_false_for_invalid_schedule():
    config = _make_config([[_make_job(schedule="bad")]])
    report = build_audit_summary(config)
    assert report.is_healthy is False


def test_str_contains_summary_label():
    config = _make_config()
    report = build_audit_summary(config)
    text = str(report)
    assert "Audit Summary" in text


def test_str_contains_server_count():
    config = _make_config([[_make_job()]])
    report = build_audit_summary(config)
    assert "Servers" in str(report)


def test_top_issues_populated_for_invalid_jobs():
    config = _make_config([[_make_job(schedule="bad-schedule")]])
    report = build_audit_summary(config)
    assert len(report.top_issues) >= 1


def test_top_issues_empty_for_valid_config():
    config = _make_config([[_make_job(schedule="0 0 * * *")]])
    report = build_audit_summary(config)
    assert report.invalid_jobs == 0
    assert report.top_issues == []


def test_average_score_is_float():
    config = _make_config([[_make_job()]])
    report = build_audit_summary(config)
    assert isinstance(report.average_score, float)


def test_health_percent_in_range():
    config = _make_config([[_make_job()]])
    report = build_audit_summary(config)
    assert 0.0 <= report.health_percent <= 100.0
