"""Generate human-readable reports from cron job audit results."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import CronJob, Server
from cronwarden.validator import ValidationResult


@dataclass
class JobReport:
    server: str
    job: CronJob
    result: ValidationResult

    @property
    def status_icon(self) -> str:
        return "✓" if self.result.valid else "✗"

    def summary_line(self) -> str:
        desc = f" — {self.job.description}" if self.job.description else ""
        return f"  [{self.status_icon}] {self.job.name}{desc} ({self.job.schedule})"


@dataclass
class ServerReport:
    server: Server
    job_reports: List[JobReport] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.job_reports)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.job_reports if r.result.valid)

    @property
    def failed(self) -> int:
        return self.total - self.passed


@dataclass
class AuditReport:
    server_reports: List[ServerReport] = field(default_factory=list)

    @property
    def total_jobs(self) -> int:
        return sum(sr.total for sr in self.server_reports)

    @property
    def total_passed(self) -> int:
        return sum(sr.passed for sr in self.server_reports)

    @property
    def total_failed(self) -> int:
        return sum(sr.failed for sr in self.server_reports)


def format_report(audit: AuditReport, verbose: bool = False) -> str:
    lines = ["CronWarden Audit Report", "=" * 40]

    for sr in audit.server_reports:
        lines.append(f"\nServer: {sr.server.host} (user: {sr.server.user})")
        lines.append(f"  Jobs: {sr.total}  Passed: {sr.passed}  Failed: {sr.failed}")

        for jr in sr.job_reports:
            lines.append(jr.summary_line())
            if not jr.result.valid:
                for err in jr.result.errors:
                    lines.append(f"      ! {err}")
            elif verbose and jr.result.warnings:
                for warn in jr.result.warnings:
                    lines.append(f"      ~ {warn}")

    lines.append("\n" + "=" * 40)
    lines.append(
        f"Total: {audit.total_jobs}  Passed: {audit.total_passed}  Failed: {audit.total_failed}"
    )
    status = "ALL CHECKS PASSED" if audit.total_failed == 0 else "SOME CHECKS FAILED"
    lines.append(status)
    return "\n".join(lines)
