"""Normalize cron job schedules to a canonical form."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob

# Map common aliases to their canonical cron expression
_ALIAS_MAP = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


@dataclass
class NormalizedJob:
    server: str
    job_name: str
    original_schedule: str
    normalized_schedule: str
    was_changed: bool

    def summary(self) -> str:
        if self.was_changed:
            return (
                f"[{self.server}] {self.job_name}: "
                f"{self.original_schedule!r} -> {self.normalized_schedule!r}"
            )
        return f"[{self.server}] {self.job_name}: unchanged ({self.normalized_schedule!r})"


@dataclass
class NormalizationResult:
    jobs: List[NormalizedJob] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(j.was_changed for j in self.jobs)

    @property
    def total_changed(self) -> int:
        return sum(1 for j in self.jobs if j.was_changed)

    @property
    def total(self) -> int:
        return len(self.jobs)

    def changed_jobs(self) -> List[NormalizedJob]:
        return [j for j in self.jobs if j.was_changed]


def _normalize_schedule(schedule: str) -> tuple[str, bool]:
    """Return (normalized_schedule, was_changed)."""
    stripped = schedule.strip()
    lower = stripped.lower()
    if lower in _ALIAS_MAP:
        canonical = _ALIAS_MAP[lower]
        return canonical, canonical != stripped
    # Normalize whitespace in standard 5-field expressions
    parts = stripped.split()
    if len(parts) == 5:
        normalized = " ".join(parts)
        return normalized, normalized != stripped
    return stripped, False


def normalize_config(config: Config) -> NormalizationResult:
    """Normalize all job schedules in the config."""
    result = NormalizationResult()
    for server in config.servers:
        for job in server.jobs:
            normalized, changed = _normalize_schedule(job.schedule)
            result.jobs.append(
                NormalizedJob(
                    server=server.name,
                    job_name=job.name,
                    original_schedule=job.schedule,
                    normalized_schedule=normalized,
                    was_changed=changed,
                )
            )
    return result
