from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob


@dataclass
class JobProfile:
    server: str
    job_name: str
    schedule: str
    command: str
    tags: List[str]
    has_description: bool
    estimated_duration: Optional[str]
    risk_level: str

    def summary(self) -> str:
        return f"{self.server}/{self.job_name} [{self.risk_level}]"


@dataclass
class ProfileResult:
    profiles: List[JobProfile] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.profiles) == 0

    def total(self) -> int:
        return len(self.profiles)

    def by_risk(self, level: str) -> List[JobProfile]:
        return [p for p in self.profiles if p.risk_level == level]


def _estimate_risk(job: CronJob) -> str:
    cmd = job.command.lower()
    if any(k in cmd for k in ("rm ", "drop ", "delete ", "truncate")):
        return "high"
    if any(k in cmd for k in ("sudo", "chmod", "chown")):
        return "medium"
    return "low"


def _estimate_duration(schedule: str) -> str:
    if schedule.startswith("*/"):
        try:
            interval = int(schedule.split("/")[1].split()[0])
            if interval <= 5:
                return "short"
        except (ValueError, IndexError):
            pass
    return "unknown"


def profile_config(config: Config) -> ProfileResult:
    result = ProfileResult()
    for server in config.servers:
        for job in server.jobs:
            profile = JobProfile(
                server=server.name,
                job_name=job.name,
                schedule=job.schedule,
                command=job.command,
                tags=job.tags or [],
                has_description=bool(job.description),
                estimated_duration=_estimate_duration(job.schedule),
                risk_level=_estimate_risk(job),
            )
            result.profiles.append(profile)
    return result
