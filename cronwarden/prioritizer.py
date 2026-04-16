from dataclasses import dataclass, field
from typing import List
from cronwarden.config import Config, CronJob


PRIORITY_KEYWORDS = {
    "critical": ["backup", "payment", "billing", "security", "alert"],
    "high": ["sync", "report", "deploy", "notify", "cleanup"],
    "medium": ["log", "cache", "index", "update"],
    "low": ["test", "debug", "temp", "sample"],
}


@dataclass
class PrioritizedJob:
    server: str
    job: CronJob
    priority: str
    reason: str

    def summary(self) -> str:
        return f"[{self.priority.upper()}] {self.server}/{self.job.name}: {self.reason}"


@dataclass
class PriorityResult:
    entries: List[PrioritizedJob] = field(default_factory=list)

    def has_critical(self) -> bool:
        return any(e.priority == "critical" for e in self.entries)

    def total(self) -> int:
        return len(self.entries)

    def by_priority(self, level: str) -> List[PrioritizedJob]:
        return [e for e in self.entries if e.priority == level]


def _detect_priority(job: CronJob) -> tuple:
    text = f"{job.name} {job.command}".lower()
    for level in ("critical", "high", "medium", "low"):
        for keyword in PRIORITY_KEYWORDS[level]:
            if keyword in text:
                return level, f"matched keyword '{keyword}'"
    return "normal", "no priority keywords matched"


def prioritize_config(config: Config) -> PriorityResult:
    result = PriorityResult()
    for server in config.servers:
        for job in server.jobs:
            priority, reason = _detect_priority(job)
            result.entries.append(
                PrioritizedJob(server=server.name, job=job, priority=priority, reason=reason)
            )
    return result
