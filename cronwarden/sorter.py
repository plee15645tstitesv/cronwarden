from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob

VALID_DIMENSIONS = ("name", "schedule", "server", "command")


@dataclass
class SortedJob:
    server: str
    job: CronJob

    def summary(self) -> str:
        return f"[{self.server}] {self.job.name} ({self.job.schedule})"


@dataclass
class SortResult:
    jobs: List[SortedJob] = field(default_factory=list)
    dimension: str = "name"
    reverse: bool = False

    def is_empty(self) -> bool:
        return len(self.jobs) == 0

    def total(self) -> int:
        return len(self.jobs)


def _job_key(sorted_job: SortedJob, dimension: str):
    if dimension == "name":
        return sorted_job.job.name.lower()
    elif dimension == "schedule":
        return sorted_job.job.schedule
    elif dimension == "server":
        return sorted_job.server.lower()
    elif dimension == "command":
        return sorted_job.job.command.lower()
    return sorted_job.job.name.lower()


def sort_config(
    config: Config,
    dimension: str = "name",
    reverse: bool = False,
) -> SortResult:
    if dimension not in VALID_DIMENSIONS:
        dimension = "name"

    flat: List[SortedJob] = []
    for server in config.servers:
        for job in server.jobs:
            flat.append(SortedJob(server=server.name, job=job))

    sorted_jobs = sorted(
        flat,
        key=lambda sj: _job_key(sj, dimension),
        reverse=reverse,
    )

    return SortResult(jobs=sorted_jobs, dimension=dimension, reverse=reverse)
