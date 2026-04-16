"""Detects cron jobs that haven't been updated or reviewed recently."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from cronwarden.config import Config, CronJob, Server


@dataclass
class StaleJob:
    server_name: str
    job: CronJob
    days_since_update: Optional[int]

    def summary(self) -> str:
        if self.days_since_update is None:
            return f"{self.job.name} on '{self.server_name}' — no last_updated set"
        return (
            f"{self.job.name} on '{self.server_name}' — "
            f"last updated {self.days_since_update} day(s) ago"
        )


@dataclass
class StalenessResult:
    stale_jobs: List[StaleJob] = field(default_factory=list)

    @property
    def has_stale(self) -> bool:
        return len(self.stale_jobs) > 0

    @property
    def total(self) -> int:
        return len(self.stale_jobs)

    def __str__(self) -> str:
        if not self.has_stale:
            return "No stale jobs found."
        lines = [f"Stale jobs ({self.total}):"]
        for entry in self.stale_jobs:
            lines.append(f"  - {entry.summary()}")
        return "\n".join(lines)


def _days_since(date_str: str, now: datetime) -> Optional[int]:
    """Parse an ISO date string and return days elapsed since then."""
    try:
        updated = datetime.fromisoformat(date_str)
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        delta = now - updated
        return max(0, delta.days)
    except (ValueError, TypeError):
        return None


def find_stale_jobs(
    config: Config,
    threshold_days: int = 90,
    now: Optional[datetime] = None,
) -> StalenessResult:
    """Return jobs whose last_updated field exceeds threshold_days, or is missing."""
    if now is None:
        now = datetime.now(tz=timezone.utc)

    stale: List[StaleJob] = []

    for server in config.servers:
        for job in server.jobs:
            last_updated = getattr(job, "last_updated", None)
            if last_updated is None:
                stale.append(StaleJob(server_name=server.name, job=job, days_since_update=None))
                continue
            days = _days_since(last_updated, now)
            if days is None or days >= threshold_days:
                stale.append(StaleJob(server_name=server.name, job=job, days_since_update=days))

    return StalenessResult(stale_jobs=stale)
