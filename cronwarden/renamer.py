"""Rename cron jobs across a config, returning a summary of changes."""
from dataclasses import dataclass, field
from typing import List
from cronwarden.config import Config, CronJob, Server


@dataclass
class RenameChange:
    server_name: str
    old_name: str
    new_name: str

    def summary(self) -> str:
        return f"[{self.server_name}] '{self.old_name}' -> '{self.new_name}'"


@dataclass
class RenameResult:
    changes: List[RenameChange] = field(default_factory=list)
    not_found: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    @property
    def total(self) -> int:
        return len(self.changes)


def rename_job(config: Config, old_name: str, new_name: str) -> RenameResult:
    """Rename all jobs matching old_name to new_name across all servers."""
    if not old_name or not new_name:
        raise ValueError("old_name and new_name must be non-empty strings")

    changes: List[RenameChange] = []
    matched = False

    for server in config.servers:
        for job in server.jobs:
            if job.name == old_name:
                matched = True
                job.name = new_name
                changes.append(RenameChange(
                    server_name=server.name,
                    old_name=old_name,
                    new_name=new_name,
                ))

    result = RenameResult(changes=changes)
    if not matched:
        result.not_found.append(old_name)
    return result
