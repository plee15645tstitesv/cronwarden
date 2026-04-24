"""Estimate total CPU/time cost of cron jobs over a given period."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob, Server


# Rough execution-time estimates (seconds) based on command heuristics
_COMMAND_WEIGHTS = {
    "rsync": 30,
    "mysqldump": 60,
    "pg_dump": 60,
    "tar": 45,
    "find": 20,
    "curl": 5,
    "wget": 5,
    "python": 10,
    "ruby": 10,
    "node": 10,
    "bash": 5,
    "sh": 5,
}
_DEFAULT_WEIGHT = 3  # seconds


@dataclass
class JobEstimate:
    server: str
    job_name: str
    schedule: str
    runs_per_day: float
    estimated_seconds_per_run: int
    estimated_seconds_per_day: float

    def summary(self) -> str:
        return (
            f"{self.server}/{self.job_name}: "
            f"{self.runs_per_day:.1f} runs/day × "
            f"{self.estimated_seconds_per_run}s = "
            f"{self.estimated_seconds_per_day:.0f}s/day"
        )


@dataclass
class EstimationResult:
    estimates: List[JobEstimate] = field(default_factory=list)
    total_seconds_per_day: float = 0.0

    @property
    def is_empty(self) -> bool:
        return len(self.estimates) == 0

    @property
    def total(self) -> int:
        return len(self.estimates)


def _runs_per_day(schedule: str) -> float:
    """Approximate how many times a cron schedule fires per day."""
    special = {
        "@yearly": 1 / 365,
        "@annually": 1 / 365,
        "@monthly": 1 / 30,
        "@weekly": 1 / 7,
        "@daily": 1.0,
        "@midnight": 1.0,
        "@hourly": 24.0,
        "@reboot": 0.0,
    }
    if schedule in special:
        return special[schedule]
    parts = schedule.split()
    if len(parts) != 5:
        return 1.0
    minute, hour = parts[0], parts[1]
    minutes = 60 if minute == "*" else (60 // int(minute.split("/")[1]) if minute.startswith("*/") else 1)
    hours = 24 if hour == "*" else (24 // int(hour.split("/")[1]) if hour.startswith("*/") else 1)
    return float(minutes * hours)


def _estimate_seconds(command: str) -> int:
    cmd_lower = command.lower()
    for keyword, weight in _COMMAND_WEIGHTS.items():
        if keyword in cmd_lower:
            return weight
    return _DEFAULT_WEIGHT


def estimate_config(config: Config) -> EstimationResult:
    estimates: List[JobEstimate] = []
    for server in config.servers:
        for job in server.jobs:
            rpd = _runs_per_day(job.schedule)
            spr = _estimate_seconds(job.command)
            spd = rpd * spr
            estimates.append(JobEstimate(
                server=server.name,
                job_name=job.name,
                schedule=job.schedule,
                runs_per_day=rpd,
                estimated_seconds_per_run=spr,
                estimated_seconds_per_day=spd,
            ))
    total = sum(e.estimated_seconds_per_day for e in estimates)
    return EstimationResult(estimates=estimates, total_seconds_per_day=total)
