from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config
from cronwarden.validator import validate_job


@dataclass
class Alert:
    server: str
    job_name: str
    level: str  # 'critical' | 'warning' | 'info'
    message: str

    def summary(self) -> str:
        return f"[{self.level.upper()}] {self.server}/{self.job_name}: {self.message}"


@dataclass
class AlertResult:
    alerts: List[Alert] = field(default_factory=list)

    @property
    def has_alerts(self) -> bool:
        return len(self.alerts) > 0

    @property
    def total(self) -> int:
        return len(self.alerts)

    def by_level(self, level: str) -> List[Alert]:
        return [a for a in self.alerts if a.level == level]

    @property
    def critical(self) -> List[Alert]:
        return self.by_level("critical")

    @property
    def warnings(self) -> List[Alert]:
        return self.by_level("warning")


def _check_job(server_name: str, job) -> List[Alert]:
    alerts: List[Alert] = []
    result = validate_job(job)
    if not result.is_valid:
        for err in result.errors:
            alerts.append(Alert(
                server=server_name,
                job_name=job.name,
                level="critical",
                message=err,
            ))
    if job.command and "sudo" in job.command:
        alerts.append(Alert(
            server=server_name,
            job_name=job.name,
            level="warning",
            message="Job uses sudo in command",
        ))
    if job.schedule == "* * * * *":
        alerts.append(Alert(
            server=server_name,
            job_name=job.name,
            level="warning",
            message="Job runs every minute; consider a less frequent schedule",
        ))
    return alerts


def check_alerts(config: Config, level_filter: Optional[str] = None) -> AlertResult:
    alerts: List[Alert] = []
    for server in config.servers:
        for job in server.jobs:
            alerts.extend(_check_job(server.name, job))
    if level_filter:
        alerts = [a for a in alerts if a.level == level_filter]
    return AlertResult(alerts=alerts)
