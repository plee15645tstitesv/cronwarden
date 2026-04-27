"""Deduplicator: identify and remove exact duplicate cron jobs across servers."""
from dataclasses import dataclass, field
from typing import List
from cronwarden.config import Config, CronJob, Server


@dataclass
class DeduplicatedJob:
    server_name: str
    job: CronJob
    duplicate_of: str  # "server_name:job_name" of the canonical original

    def summary(self) -> str:
        return f"[{self.server_name}] {self.job.name} is a duplicate of {self.duplicate_of}"


@dataclass
class DeduplicationResult:
    duplicates: List[DeduplicatedJob] = field(default_factory=list)
    total_jobs_scanned: int = 0

    @property
    def has_duplicates(self) -> bool:
        return len(self.duplicates) > 0

    @property
    def total(self) -> int:
        return len(self.duplicates)

    def is_empty(self) -> bool:
        return self.total_jobs_scanned == 0


def _job_key(job: CronJob) -> str:
    """Return a canonical key representing the job's identity."""
    return f"{job.schedule.strip()}::{job.command.strip()}"


def deduplicate_config(config: Config) -> DeduplicationResult:
    """Scan all jobs across all servers and flag exact duplicates.

    Two jobs are considered duplicates if they share the same schedule
    and command, regardless of name or server.
    """
    seen: dict = {}  # key -> "server_name:job_name"
    duplicates: List[DeduplicatedJob] = []
    total = 0

    for server in config.servers:
        for job in server.jobs:
            total += 1
            key = _job_key(job)
            canonical = f"{server.name}:{job.name}"
            if key in seen:
                duplicates.append(
                    DeduplicatedJob(
                        server_name=server.name,
                        job=job,
                        duplicate_of=seen[key],
                    )
                )
            else:
                seen[key] = canonical

    return DeduplicationResult(duplicates=duplicates, total_jobs_scanned=total)
