"""Summarizer module: generates a high-level health summary of all cron jobs."""

from dataclasses import dataclass, field
from typing import List

from cronwarden.config import Config
from cronwarden.auditor import audit_config
from cronwarden.reporter import ServerReport


@dataclass
class SummaryStats:
    total_servers: int = 0
    total_jobs: int = 0
    valid_jobs: int = 0
    invalid_jobs: int = 0
    servers_with_failures: List[str] = field(default_factory=list)

    @property
    def health_percent(self) -> float:
        if self.total_jobs == 0:
            return 100.0
        return round((self.valid_jobs / self.total_jobs) * 100, 1)

    @property
    def is_healthy(self) -> bool:
        return self.invalid_jobs == 0

    def __str__(self) -> str:
        status = "HEALTHY" if self.is_healthy else "DEGRADED"
        lines = [
            f"Status      : {status}",
            f"Servers     : {self.total_servers}",
            f"Total Jobs  : {self.total_jobs}",
            f"Valid       : {self.valid_jobs}",
            f"Invalid     : {self.invalid_jobs}",
            f"Health      : {self.health_percent}%",
        ]
        if self.servers_with_failures:
            lines.append("Failing on  : " + ", ".join(self.servers_with_failures))
        return "\n".join(lines)


def summarize(config: Config) -> SummaryStats:
    """Audit the config and return aggregated SummaryStats."""
    reports: List[ServerReport] = audit_config(config)
    stats = SummaryStats(total_servers=len(reports))

    for report in reports:
        has_failure = False
        for job_report in report.job_reports:
            stats.total_jobs += 1
            if job_report.result.is_valid:
                stats.valid_jobs += 1
            else:
                stats.invalid_jobs += 1
                has_failure = True
        if has_failure:
            stats.servers_with_failures.append(report.server.name)

    return stats
