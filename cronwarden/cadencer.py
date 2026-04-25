"""cadencer.py — Detect jobs whose schedules run too frequently or too close together."""

from dataclasses import dataclass, field
from typing import List
from cronwarden.config import Config, CronJob, Server
from cronwarden.estimator import runs_per_day


HIGH_FREQUENCY_THRESHOLD = 96  # more than every 15 minutes
CLOSE_INTERVAL_MINUTES = 5     # jobs on same server within 5 minutes of each other


@dataclass
class CadenceIssue:
    server: str
    job_name: str
    schedule: str
    issue: str
    runs_per_day: float

    def summary(self) -> str:
        return f"[{self.server}] {self.job_name} ({self.schedule}): {self.issue}"


@dataclass
class CadenceResult:
    issues: List[CadenceIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def total(self) -> int:
        return len(self.issues)


def _parse_minute(minute_field: str) -> List[int]:
    """Return the set of minutes a field resolves to (0-59)."""
    if minute_field == "*":
        return list(range(60))
    minutes = []
    for part in minute_field.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            start = 0 if base == "*" else int(base)
            minutes.extend(range(start, 60, int(step)))
        elif "-" in part:
            lo, hi = part.split("-", 1)
            minutes.extend(range(int(lo), int(hi) + 1))
        else:
            minutes.append(int(part))
    return sorted(set(minutes))


def _min_gap_minutes(schedule: str) -> int:
    """Return the minimum gap in minutes between any two consecutive triggers in an hour."""
    parts = schedule.strip().split()
    if len(parts) != 5 or parts[0] in ("@reboot", "@yearly", "@annually",
                                        "@monthly", "@weekly", "@daily",
                                        "@midnight", "@hourly"):
        return 60
    minutes = _parse_minute(parts[0])
    if len(minutes) <= 1:
        return 60
    gaps = [minutes[i + 1] - minutes[i] for i in range(len(minutes) - 1)]
    return min(gaps)


def check_cadence(config: Config) -> CadenceResult:
    result = CadenceResult()
    for server in config.servers:
        for job in server.jobs:
            try:
                rpd = runs_per_day(job.schedule)
            except Exception:
                rpd = 0.0

            if rpd > HIGH_FREQUENCY_THRESHOLD:
                result.issues.append(CadenceIssue(
                    server=server.name,
                    job_name=job.name,
                    schedule=job.schedule,
                    issue=f"runs ~{rpd:.0f}x/day (exceeds threshold of {HIGH_FREQUENCY_THRESHOLD})",
                    runs_per_day=rpd,
                ))
                continue

            gap = _min_gap_minutes(job.schedule)
            if 0 < gap < CLOSE_INTERVAL_MINUTES:
                result.issues.append(CadenceIssue(
                    server=server.name,
                    job_name=job.name,
                    schedule=job.schedule,
                    issue=f"triggers repeat within {gap} minute(s) of each other",
                    runs_per_day=rpd,
                ))
    return result
