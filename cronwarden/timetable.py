"""Timetable: build a human-readable schedule grid for all jobs across servers."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from cronwarden.config import Config


HOURS = list(range(24))


@dataclass
class TimetableEntry:
    server: str
    job_name: str
    schedule: str
    hours: List[int]  # hours of day this job fires (best-effort)

    def summary(self) -> str:
        hour_str = ", ".join(str(h) for h in self.hours) if self.hours else "varies"
        return f"{self.server}/{self.job_name} [{self.schedule}] -> hours: {hour_str}"


@dataclass
class TimetableResult:
    entries: List[TimetableEntry] = field(default_factory=list)
    grid: Dict[int, List[str]] = field(default_factory=dict)  # hour -> list of job labels

    @property
    def is_empty(self) -> bool:
        return len(self.entries) == 0

    @property
    def total(self) -> int:
        return len(self.entries)

    def busiest_hour(self) -> Optional[int]:
        if not self.grid:
            return None
        return max(self.grid, key=lambda h: len(self.grid[h]))


def _parse_hour_field(field_val: str) -> List[int]:
    """Return list of hours (0-23) that match the cron hour field."""
    if field_val == "*":
        return list(range(24))
    hours = []
    for part in field_val.split(","):
        part = part.strip()
        if "/" in part:
            base, step = part.split("/", 1)
            try:
                step = int(step)
                start = 0 if base == "*" else int(base)
                hours.extend(range(start, 24, step))
            except ValueError:
                pass
        elif "-" in part:
            try:
                lo, hi = part.split("-", 1)
                hours.extend(range(int(lo), int(hi) + 1))
            except ValueError:
                pass
        else:
            try:
                hours.append(int(part))
            except ValueError:
                pass
    return sorted(set(h for h in hours if 0 <= h <= 23))


def build_timetable(config: Config) -> TimetableResult:
    """Build a timetable from a Config, mapping jobs to hours of the day."""
    entries: List[TimetableEntry] = []
    grid: Dict[int, List[str]] = {h: [] for h in range(24)}

    for server in config.servers:
        for job in server.jobs:
            schedule = job.schedule.strip()
            # Handle special aliases
            if schedule in ("@daily", "@midnight"):
                hours = [0]
            elif schedule == "@hourly":
                hours = list(range(24))
            elif schedule == "@weekly":
                hours = [0]
            elif schedule == "@monthly":
                hours = [0]
            elif schedule == "@yearly" or schedule == "@annually":
                hours = [0]
            elif schedule == "@reboot":
                hours = []
            else:
                parts = schedule.split()
                if len(parts) >= 2:
                    hours = _parse_hour_field(parts[1])
                else:
                    hours = []

            label = f"{server.name}/{job.name}"
            entry = TimetableEntry(
                server=server.name,
                job_name=job.name,
                schedule=schedule,
                hours=hours,
            )
            entries.append(entry)
            for h in hours:
                grid[h].append(label)

    # Remove empty hours from grid for cleanliness
    grid = {h: jobs for h, jobs in grid.items() if jobs}
    return TimetableResult(entries=entries, grid=grid)
