from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, Server, CronJob


@dataclass
class ClonedJob:
    source_server: str
    target_server: str
    job_name: str
    schedule: str
    command: str

    def summary(self) -> str:
        return f"{self.job_name} cloned from {self.source_server} to {self.target_server}"


@dataclass
class CloneResult:
    cloned: List[ClonedJob] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_clones(self) -> bool:
        return len(self.cloned) > 0

    @property
    def total(self) -> int:
        return len(self.cloned)


def clone_jobs(
    config: Config,
    job_names: List[str],
    source_server: str,
    target_server: str,
) -> CloneResult:
    result = CloneResult()

    source: Optional[Server] = next(
        (s for s in config.servers if s.name == source_server), None
    )
    target: Optional[Server] = next(
        (s for s in config.servers if s.name == target_server), None
    )

    if source is None or target is None:
        return result

    existing_names = {j.name for j in target.jobs}

    for job in source.jobs:
        if job.name not in job_names:
            continue
        if job.name in existing_names:
            result.skipped.append(job.name)
            continue
        cloned_job = CronJob(
            name=job.name,
            schedule=job.schedule,
            command=job.command,
            description=job.description,
            tags=list(job.tags) if job.tags else [],
        )
        target.jobs.append(cloned_job)
        result.cloned.append(
            ClonedJob(
                source_server=source_server,
                target_server=target_server,
                job_name=job.name,
                schedule=job.schedule,
                command=job.command,
            )
        )

    return result
