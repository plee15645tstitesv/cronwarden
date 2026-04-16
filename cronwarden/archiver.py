"""Archive (disable/enable) cron jobs by injecting or removing comment markers."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import CronJob, Server, Config

ARCHIVE_MARKER = "#CRONWARDEN:ARCHIVED"


@dataclass
class ArchivedJob:
    server_name: str
    job_name: str
    original_command: str
    archived_command: str

    @property
    def summary(self) -> str:
        return f"[{self.server_name}] {self.job_name}: archived"


@dataclass
class ArchiveResult:
    archived: List[ArchivedJob] = field(default_factory=list)
    restored: List[ArchivedJob] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.archived or self.restored)

    @property
    def total_archived(self) -> int:
        return len(self.archived)

    @property
    def total_restored(self) -> int:
        return len(self.restored)


def _is_archived(command: str) -> bool:
    return command.strip().startswith(ARCHIVE_MARKER)


def _archive_command(command: str) -> str:
    return f"{ARCHIVE_MARKER} {command}"


def _restore_command(command: str) -> str:
    return command.replace(ARCHIVE_MARKER, "", 1).strip()


def archive_jobs(config: Config, job_names: List[str], server_name: Optional[str] = None) -> ArchiveResult:
    """Mark matching jobs as archived by prefixing their command with the archive marker."""
    result = ArchiveResult()
    for server in config.servers:
        if server_name and server.name != server_name:
            continue
        for job in server.jobs:
            if job.name not in job_names:
                continue
            if _is_archived(job.command):
                result.skipped.append(f"[{server.name}] {job.name} already archived")
                continue
            archived_cmd = _archive_command(job.command)
            result.archived.append(ArchivedJob(
                server_name=server.name,
                job_name=job.name,
                original_command=job.command,
                archived_command=archived_cmd,
            ))
            job.command = archived_cmd
    return result


def restore_jobs(config: Config, job_names: List[str], server_name: Optional[str] = None) -> ArchiveResult:
    """Restore previously archived jobs by removing the archive marker from their command."""
    result = ArchiveResult()
    for server in config.servers:
        if server_name and server.name != server_name:
            continue
        for job in server.jobs:
            if job.name not in job_names:
                continue
            if not _is_archived(job.command):
                result.skipped.append(f"[{server.name}] {job.name} is not archived")
                continue
            restored_cmd = _restore_command(job.command)
            result.restored.append(ArchivedJob(
                server_name=server.name,
                job_name=job.name,
                original_command=job.command,
                archived_command=restored_cmd,
            ))
            job.command = restored_cmd
    return result
