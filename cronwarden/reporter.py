"""Build structured report objects from audit results."""

from dataclasses import dataclass, field
from typing import List

from cronwarden.config import CronJob, Server
from cronwarden.validator import ValidationResult
from cronwarden.explainer import explain_schedule


@dataclass
class JobReport:
    job: CronJob
    result: ValidationResult

    @property
    def status_icon(self) -> str:
        return "✅" if self.result.valid else "❌"

    @property
    def summary_line(self) -> str:
        explanation = explain_schedule(self.job.schedule)
        status = "OK" if self.result.valid else "; ".join(self.result.errors)
        return f"{self.status_icon} [{self.job.name}] {self.job.schedule} — {explanation} | {status}"

    @property
    def schedule_explanation(self) -> str:
        return explain_schedule(self.job.schedule)


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

    @property
    def has_failures(self) -> bool:
        return self.failed > 0

    def add(self, job: CronJob, result: ValidationResult) -> None:
        self.job_reports.append(JobReport(job=job, result=result))


def build_server_report(server: Server, results: dict) -> ServerReport:
    """Construct a ServerReport from a server and a mapping of job -> ValidationResult."""
    report = ServerReport(server=server)
    for job, result in results.items():
        report.add(job, result)
    return report
