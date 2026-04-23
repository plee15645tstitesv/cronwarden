"""Rotator: detect jobs whose schedules should be staggered to reduce load spikes."""
from dataclasses import dataclass, field
from typing import List
from cronwarden.config import Config, CronJob


@dataclass
class RotationSuggestion:
    server: str
    job_name: str
    current_schedule: str
    suggested_schedule: str
    reason: str

    def summary(self) -> str:
        return (
            f"[{self.server}] {self.job_name}: "
            f"{self.current_schedule!r} -> {self.suggested_schedule!r} ({self.reason})"
        )


@dataclass
class RotationResult:
    suggestions: List[RotationSuggestion] = field(default_factory=list)

    @property
    def has_suggestions(self) -> bool:
        return len(self.suggestions) > 0

    @property
    def total(self) -> int:
        return len(self.suggestions)

    def __str__(self) -> str:
        if not self.has_suggestions:
            return "No rotation suggestions."
        lines = [f"{len(self.suggestions)} rotation suggestion(s):"]
        for s in self.suggestions:
            lines.append(f"  - {s.summary()}")
        return "\n".join(lines)


def _parse_minute(schedule: str) -> int:
    """Return the minute field as an int, or -1 if not a fixed minute."""
    parts = schedule.strip().split()
    if len(parts) != 5:
        return -1
    minute = parts[0]
    if minute.isdigit():
        return int(minute)
    return -1


def _suggest_offset(minute: int, index: int, total: int) -> int:
    """Spread jobs evenly within the hour."""
    if total <= 1:
        return minute
    step = max(1, 60 // total)
    return (minute + index * step) % 60


def rotate_config(config: Config) -> RotationResult:
    """Suggest schedule rotations for jobs that share the same fixed minute."""
    # Group jobs by their fixed minute value across all servers
    from collections import defaultdict
    minute_groups: dict = defaultdict(list)  # minute -> [(server_name, job)]

    for server in config.servers:
        for job in server.jobs:
            minute = _parse_minute(job.schedule)
            if minute >= 0:
                minute_groups[minute].append((server.name, job))

    suggestions: List[RotationSuggestion] = []

    for minute, entries in minute_groups.items():
        if len(entries) < 2:
            continue
        for idx, (server_name, job) in enumerate(entries):
            if idx == 0:
                continue  # keep the first job as-is
            parts = job.schedule.strip().split()
            new_minute = _suggest_offset(minute, idx, len(entries))
            if new_minute == minute:
                continue
            parts[0] = str(new_minute)
            suggested = " ".join(parts)
            suggestions.append(
                RotationSuggestion(
                    server=server_name,
                    job_name=job.name,
                    current_schedule=job.schedule,
                    suggested_schedule=suggested,
                    reason=f"{len(entries)} jobs share minute :{minute:02d}",
                )
            )

    return RotationResult(suggestions=suggestions)
