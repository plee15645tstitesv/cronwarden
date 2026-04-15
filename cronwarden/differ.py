"""Diff cron job configurations between two config files or snapshots."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob


@dataclass
class JobDiff:
    server: str
    job_name: str
    kind: str  # 'added', 'removed', 'changed'
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None

    def summary(self) -> str:
        if self.kind == "added":
            return f"[+] {self.server}/{self.job_name}: added"
        if self.kind == "removed":
            return f"[-] {self.server}/{self.job_name}: removed"
        changes = []
        old = self.old_value or {}
        new = self.new_value or {}
        for key in set(list(old.keys()) + list(new.keys())):
            if old.get(key) != new.get(key):
                changes.append(f"{key}: '{old.get(key)}' -> '{new.get(key)}'")
        return f"[~] {self.server}/{self.job_name}: " + ", ".join(changes)


@dataclass
class DiffResult:
    diffs: List[JobDiff] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.diffs) > 0

    def added(self) -> List[JobDiff]:
        return [d for d in self.diffs if d.kind == "added"]

    def removed(self) -> List[JobDiff]:
        return [d for d in self.diffs if d.kind == "removed"]

    def changed(self) -> List[JobDiff]:
        return [d for d in self.diffs if d.kind == "changed"]


def _job_to_dict(job: CronJob) -> dict:
    return {
        "schedule": job.schedule,
        "command": job.command,
        "description": job.description,
    }


def diff_configs(old: Config, new: Config) -> DiffResult:
    """Compare two Config objects and return a DiffResult with all changes."""
    result = DiffResult()

    old_jobs: dict = {}
    for server in old.servers:
        for job in server.jobs:
            old_jobs[(server.name, job.name)] = job

    new_jobs: dict = {}
    for server in new.servers:
        for job in server.jobs:
            new_jobs[(server.name, job.name)] = job

    all_keys = set(old_jobs.keys()) | set(new_jobs.keys())

    for key in sorted(all_keys):
        server_name, job_name = key
        if key in old_jobs and key not in new_jobs:
            result.diffs.append(JobDiff(
                server=server_name, job_name=job_name, kind="removed",
                old_value=_job_to_dict(old_jobs[key])
            ))
        elif key not in old_jobs and key in new_jobs:
            result.diffs.append(JobDiff(
                server=server_name, job_name=job_name, kind="added",
                new_value=_job_to_dict(new_jobs[key])
            ))
        else:
            old_d = _job_to_dict(old_jobs[key])
            new_d = _job_to_dict(new_jobs[key])
            if old_d != new_d:
                result.diffs.append(JobDiff(
                    server=server_name, job_name=job_name, kind="changed",
                    old_value=old_d, new_value=new_d
                ))

    return result
