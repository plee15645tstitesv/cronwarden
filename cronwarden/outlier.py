"""Detect outlier cron jobs based on unusual scheduling patterns."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config


@dataclass
class OutlierJob:
    server: str
    job_name: str
    schedule: str
    reason: str
    severity: str  # "low", "medium", "high"

    def summary(self) -> str:
        return f"[{self.severity.upper()}] {self.server}/{self.job_name} ({self.schedule}): {self.reason}"


@dataclass
class OutlierResult:
    outliers: List[OutlierJob] = field(default_factory=list)

    @property
    def has_outliers(self) -> bool:
        return len(self.outliers) > 0

    @property
    def total(self) -> int:
        return len(self.outliers)

    def by_severity(self, severity: str) -> List[OutlierJob]:
        return [o for o in self.outliers if o.severity == severity]


def _parse_minute(field: str) -> List[int]:
    if field == "*":
        return list(range(60))
    minutes = []
    for part in field.split(","):
        if "/" in part:
            base, step = part.split("/", 1)
            start = 0 if base == "*" else int(base.lstrip("*"))
            minutes.extend(range(start, 60, int(step)))
        elif "-" in part:
            lo, hi = part.split("-", 1)
            minutes.extend(range(int(lo), int(hi) + 1))
        else:
            minutes.append(int(part))
    return minutes


def _detect_outliers(server: str, job_name: str, schedule: str) -> List[OutlierJob]:
    found: List[OutlierJob] = []
    if schedule.startswith("@"):
        return found
    parts = schedule.split()
    if len(parts) != 5:
        return found
    minute_field = parts[0]
    hour_field = parts[1]

    # High-frequency: runs every minute
    if minute_field == "*" and hour_field == "*":
        found.append(OutlierJob(server, job_name, schedule,
                                "Runs every minute — extremely high frequency", "high"))
        return found

    # Runs multiple times per hour but not every minute
    if "/" in minute_field:
        try:
            step = int(minute_field.split("/")[1])
            if step <= 5:
                found.append(OutlierJob(server, job_name, schedule,
                                        f"Runs every {step} minutes — very high frequency", "medium"))
        except ValueError:
            pass

    # Odd minute value (e.g. :37, :53) suggests copy-paste without adjustment
    if minute_field.isdigit():
        m = int(minute_field)
        if m not in (0, 5, 10, 15, 20, 25, 30, 45) and m > 1:
            found.append(OutlierJob(server, job_name, schedule,
                                    f"Unusual minute value :{m} — possible copy-paste error", "low"))
    return found


def find_outliers(config: Config) -> OutlierResult:
    result = OutlierResult()
    for server in config.servers:
        for job in server.jobs:
            result.outliers.extend(_detect_outliers(server.name, job.name, job.schedule))
    return result
