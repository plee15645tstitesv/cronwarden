from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob


@dataclass
class PausedJob:
    server: str
    job_name: str
    schedule: str
    command: str
    reason: Optional[str] = None

    def summary(self) -> str:
        reason_part = f" ({self.reason})" if self.reason else ""
        return f"[{self.server}] {self.job_name}{reason_part}"


@dataclass
class PauseResult:
    paused: List[PausedJob] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_paused(self) -> bool:
        return len(self.paused) > 0

    @property
    def total(self) -> int:
        return len(self.paused)


def pause_jobs(
    config: Config,
    job_names: List[str],
    reason: Optional[str] = None,
) -> PauseResult:
    """Mark jobs as paused by matching name across all servers."""
    result = PauseResult()
    matched = set()

    for server in config.servers:
        for job in server.jobs:
            if job.name in job_names:
                result.paused.append(
                    PausedJob(
                        server=server.name,
                        job_name=job.name,
                        schedule=job.schedule,
                        command=job.command,
                        reason=reason,
                    )
                )
                matched.add(job.name)

    for name in job_names:
        if name not in matched:
            result.skipped.append(name)

    return result
