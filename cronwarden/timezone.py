"""Timezone-awareness module for cronwarden.

Provides utilities to annotate cron jobs with timezone information
and detect jobs that lack timezone context.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from cronwarden.config import Config, CronJob


@dataclass
class TimezoneAnnotation:
    server: str
    job_name: str
    command: str
    schedule: str
    timezone: Optional[str]
    inferred: bool

    def summary(self) -> str:
        tz = self.timezone or "unknown"
        source = "(inferred)" if self.inferred else "(explicit)"
        return f"{self.server}/{self.job_name}: tz={tz} {source}"


@dataclass
class TimezoneResult:
    annotations: List[TimezoneAnnotation] = field(default_factory=list)

    @property
    def has_missing(self) -> bool:
        return any(a.timezone is None for a in self.annotations)

    @property
    def total(self) -> int:
        return len(self.annotations)

    @property
    def missing_count(self) -> int:
        return sum(1 for a in self.annotations if a.timezone is None)

    def jobs_without_timezone(self) -> List[TimezoneAnnotation]:
        return [a for a in self.annotations if a.timezone is None]


def _extract_timezone(job: CronJob, server_tz: Optional[str]) -> tuple[Optional[str], bool]:
    """Return (timezone, inferred) for a job."""
    tags = job.tags or []
    for tag in tags:
        if tag.startswith("tz:"):
            return tag[3:].strip(), False
    if server_tz:
        return server_tz, True
    return None, False


def annotate_timezones(config: Config, default_tz: Optional[str] = None) -> TimezoneResult:
    """Annotate all jobs in the config with timezone information."""
    result = TimezoneResult()
    for server in config.servers:
        server_tz = getattr(server, "timezone", None) or default_tz
        for job in server.jobs:
            tz, inferred = _extract_timezone(job, server_tz)
            annotation = TimezoneAnnotation(
                server=server.name,
                job_name=job.name,
                command=job.command,
                schedule=job.schedule,
                timezone=tz,
                inferred=inferred,
            )
            result.annotations.append(annotation)
    return result
