"""trimmer.py — Remove jobs from a config that match given criteria (name, tag, or command pattern)."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob, Server


@dataclass
class TrimmedJob:
    server: str
    job_name: str
    reason: str

    def summary(self) -> str:
        return f"[{self.server}] {self.job_name} — {self.reason}"


@dataclass
class TrimResult:
    trimmed: List[TrimmedJob] = field(default_factory=list)
    config: Optional[Config] = None

    @property
    def has_trimmed(self) -> bool:
        return len(self.trimmed) > 0

    @property
    def total(self) -> int:
        return len(self.trimmed)

    def __str__(self) -> str:
        if not self.has_trimmed:
            return "No jobs trimmed."
        lines = [f"Trimmed {self.total} job(s):"]
        for t in self.trimmed:
            lines.append(f"  - {t.summary()}")
        return "\n".join(lines)


def _job_matches(
    job: CronJob,
    names: Optional[List[str]],
    tags: Optional[List[str]],
    command_pattern: Optional[str],
) -> Optional[str]:
    if names and job.name in names:
        return f"name match: {job.name}"
    if tags and job.tags:
        for tag in tags:
            if tag in job.tags:
                return f"tag match: {tag}"
    if command_pattern and command_pattern in job.command:
        return f"command pattern match: {command_pattern}"
    return None


def trim_config(
    config: Config,
    names: Optional[List[str]] = None,
    tags: Optional[List[str]] = None,
    command_pattern: Optional[str] = None,
) -> TrimResult:
    trimmed: List[TrimmedJob] = []
    new_servers: List[Server] = []

    for server in config.servers:
        kept_jobs: List[CronJob] = []
        for job in server.jobs:
            reason = _job_matches(job, names, tags, command_pattern)
            if reason:
                trimmed.append(TrimmedJob(server=server.name, job_name=job.name, reason=reason))
            else:
                kept_jobs.append(job)
        new_servers.append(Server(name=server.name, host=server.host, jobs=kept_jobs))

    new_config = Config(servers=new_servers)
    return TrimResult(trimmed=trimmed, config=new_config)
