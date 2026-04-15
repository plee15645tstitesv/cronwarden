"""Detect duplicate or near-duplicate cron jobs across servers."""

from dataclasses import dataclass, field
from typing import List, Tuple
from cronwarden.config import Config, CronJob, Server


@dataclass
class DuplicateGroup:
    """A group of jobs that share the same schedule and command."""
    schedule: str
    command: str
    jobs: List[Tuple[Server, CronJob]] = field(default_factory=list)

    @property
    def summary(self) -> str:
        servers = ", ".join(s.name for s, _ in self.jobs)
        return f"[{self.schedule}] `{self.command}` — found on: {servers}"


@dataclass
class DuplicateResult:
    """Result of a duplicate detection scan."""
    groups: List[DuplicateGroup] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return len(self.groups) > 0

    @property
    def total(self) -> int:
        return len(self.groups)

    def __str__(self) -> str:
        if not self.has_duplicates:
            return "No duplicate jobs found."
        lines = [f"{self.total} duplicate group(s) detected:"]
        for g in self.groups:
            lines.append(f"  - {g.summary}")
        return "\n".join(lines)


def find_duplicates(config: Config) -> DuplicateResult:
    """Find jobs with identical schedule+command across all servers."""
    seen: dict = {}

    for server in config.servers:
        for job in server.jobs:
            key = (job.schedule.strip(), job.command.strip())
            if key not in seen:
                seen[key] = DuplicateGroup(schedule=key[0], command=key[1])
            seen[key].jobs.append((server, job))

    groups = [g for g in seen.values() if len(g.jobs) > 1]
    return DuplicateResult(groups=groups)
