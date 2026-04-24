"""Detect jobs whose schedules form cyclical or overlapping execution windows."""
from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob, Server


@dataclass
class CycleEntry:
    server: str
    job_name: str
    schedule: str
    overlap_with: str
    overlap_job: str
    reason: str

    def summary(self) -> str:
        return (
            f"[{self.server}] '{self.job_name}' ({self.schedule}) overlaps with "
            f"'{self.overlap_job}' ({self.overlap_with}): {self.reason}"
        )


@dataclass
class CycleResult:
    entries: List[CycleEntry] = field(default_factory=list)

    @property
    def has_cycles(self) -> bool:
        return len(self.entries) > 0

    @property
    def total(self) -> int:
        return len(self.entries)


def _parse_minute(expr: str) -> Optional[int]:
    """Return a fixed minute value or None if wildcard/step."""
    if expr == "*" or "/" in expr:
        return None
    try:
        return int(expr)
    except ValueError:
        return None


def _parse_hour(expr: str) -> Optional[int]:
    """Return a fixed hour value or None if wildcard/step."""
    if expr == "*" or "/" in expr:
        return None
    try:
        return int(expr)
    except ValueError:
        return None


def _schedules_overlap(a: str, b: str) -> Optional[str]:
    """Return a reason string if two schedules overlap, else None."""
    if a == b:
        return "identical schedules"
    parts_a = a.strip().split()
    parts_b = b.strip().split()
    if len(parts_a) != 5 or len(parts_b) != 5:
        return None
    min_a, hr_a = _parse_minute(parts_a[0]), _parse_hour(parts_a[1])
    min_b, hr_b = _parse_minute(parts_b[0]), _parse_hour(parts_b[1])
    # Both run every minute of every hour
    if parts_a[0] == "*" and parts_b[0] == "*":
        return "both run every minute"
    # Same fixed minute and hour
    if min_a is not None and min_a == min_b and hr_a is not None and hr_a == hr_b:
        return f"same execution time ({hr_a:02d}:{min_a:02d})"
    return None


def detect_cycles(config: Config) -> CycleResult:
    """Detect overlapping/cyclical schedules across all jobs in the config."""
    result = CycleResult()
    seen: List[tuple] = []  # (server_name, job, schedule)

    for server in config.servers:
        for job in server.jobs:
            for prev_server, prev_job, prev_schedule in seen:
                reason = _schedules_overlap(job.schedule, prev_schedule)
                if reason:
                    result.entries.append(CycleEntry(
                        server=server.name,
                        job_name=job.name,
                        schedule=job.schedule,
                        overlap_with=prev_schedule,
                        overlap_job=prev_job,
                        reason=reason,
                    ))
            seen.append((server.name, job.name, job.schedule))

    return result
