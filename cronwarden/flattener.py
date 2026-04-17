"""Flatten all cron jobs from a config into a single list with server context."""
from dataclasses import dataclass
from typing import List, Optional
from cronwarden.config import Config, CronJob


@dataclass
class FlatJob:
    server: str
    name: str
    schedule: str
    command: str
    description: Optional[str]
    tags: List[str]

    def summary(self) -> str:
        tag_str = ", ".join(self.tags) if self.tags else "(none)"
        return f"[{self.server}] {self.name} | {self.schedule} | {self.command} | tags: {tag_str}"


@dataclass
class FlatResult:
    jobs: List[FlatJob]

    @property
    def total(self) -> int:
        return len(self.jobs)

    @property
    def is_empty(self) -> bool:
        return self.total == 0

    def for_server(self, server: str) -> List[FlatJob]:
        return [j for j in self.jobs if j.server == server]

    def with_tag(self, tag: str) -> List[FlatJob]:
        return [j for j in self.jobs if tag in j.tags]


def flatten_config(config: Config) -> FlatResult:
    jobs: List[FlatJob] = []
    for server in config.servers:
        for job in server.jobs:
            jobs.append(FlatJob(
                server=server.name,
                name=job.name,
                schedule=job.schedule,
                command=job.command,
                description=job.description,
                tags=list(job.tags) if job.tags else [],
            ))
    return FlatResult(jobs=jobs)
