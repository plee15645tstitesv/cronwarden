"""Orchestrate validation of all cron jobs across configured servers."""

from cronwarden.config import Config
from cronwarden.validator import validate_job
from cronwarden.reporter import AuditReport, JobReport, ServerReport


def audit_config(config: Config) -> AuditReport:
    """Run validation on every job in every server and return an AuditReport."""
    audit = AuditReport()

    for server in config.servers:
        server_report = ServerReport(server=server)
        jobs = server.jobs if server.jobs else config.jobs

        for job in jobs:
            result = validate_job(job)
            server_report.job_reports.append(
                JobReport(server=server.host, job=job, result=result)
            )

        audit.server_reports.append(server_report)

    return audit


def has_failures(audit: AuditReport) -> bool:
    """Return True if any job in the audit failed validation."""
    return audit.total_failed > 0
