"""Mirror cron jobs from one server definition to another within a config."""
from dataclasses import dataclass
from typing import List, Optional
from cronwarden.config import Config, CronJob, Server


@dataclass
class MirroredJob:
    source_server: str
    target_server: str
    job_name: str
    schedule: str
    command: str

    def summary(self) -> str:
        return f"{self.job_name} ({self.schedule}) mirrored from '{self.source_server}' to '{self.target_server}'"


@dataclass
class MirrorResult:
    mirrored: List[MirroredJob]
    source_server: str
    target_server: str

    @property
    def has_mirrored(self) -> bool:
        return len(self.mirrored) > 0

    @property
    def total(self) -> int:
        return len(self.mirrored)


def mirror_jobs(
    config: Config,
    source_name: str,
    target_name: str,
    name_filter: Optional[str] = None,
) -> MirrorResult:
    """Copy jobs from source server to target server in a new Config.

    Returns a MirrorResult describing what would be mirrored.
    Raises ValueError if source or target server is not found.
    """
    source: Optional[Server] = None
    target: Optional[Server] = None

    for server in config.servers:
        if server.name == source_name:
            source = server
        if server.name == target_name:
            target = server

    if source is None:
        raise ValueError(f"Source server '{source_name}' not found in config.")
    if target is None:
        raise ValueError(f"Target server '{target_name}' not found in config.")

    mirrored: List[MirroredJob] = []
    for job in source.jobs:
        if name_filter and name_filter.lower() not in job.name.lower():
            continue
        mirrored.append(
            MirroredJob(
                source_server=source_name,
                target_server=target_name,
                job_name=job.name,
                schedule=job.schedule,
                command=job.command,
            )
        )

    return MirrorResult(
        mirrored=mirrored,
        source_server=source_name,
        target_server=target_name,
    )
