from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: int = 60


@dataclass
class RetriedJob:
    server: str
    job_name: str
    command: str
    schedule: str
    max_attempts: int
    backoff_seconds: int
    tags: List[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"{self.server}/{self.job_name}: retry up to {self.max_attempts}x "
            f"every {self.backoff_seconds}s"
        )


@dataclass
class RetryResult:
    jobs: List[RetriedJob] = field(default_factory=list)

    def has_retries(self) -> bool:
        return len(self.jobs) > 0

    def total(self) -> int:
        return len(self.jobs)


def apply_retry_policy(
    config: Config,
    policy: Optional[RetryPolicy] = None,
    tags: Optional[List[str]] = None,
) -> RetryResult:
    if policy is None:
        policy = RetryPolicy()

    result = RetryResult()
    for server in config.servers:
        for job in server.jobs:
            if tags and not any(t in (job.tags or []) for t in tags):
                continue
            result.jobs.append(
                RetriedJob(
                    server=server.name,
                    job_name=job.name,
                    command=job.command,
                    schedule=job.schedule,
                    max_attempts=policy.max_attempts,
                    backoff_seconds=policy.backoff_seconds,
                    tags=job.tags or [],
                )
            )
    return result
