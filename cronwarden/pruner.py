"""Pruner: identify and remove jobs that have never run or are considered dead weight."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob, Server


@dataclass
class PrunedJob:
    server: str
    job_name: str
    schedule: str
    command: str
    reason: str

    def summary(self) -> str:
        return f"[{self.server}] {self.job_name} — {self.reason}"


@dataclass
class PruneResult:
    pruned: List[PrunedJob] = field(default_factory=list)
    total_scanned: int = 0

    def has_pruned(self) -> bool:
        return len(self.pruned) > 0

    def total(self) -> int:
        return len(self.pruned)

    def __str__(self) -> str:
        if not self.pruned:
            return "No jobs flagged for pruning."
        lines = [f"Pruning candidates ({self.total()}/{self.total_scanned}):"] + [
            f"  - {p.summary()}" for p in self.pruned
        ]
        return "\n".join(lines)


def _should_prune(job: CronJob, never_run_names: Optional[List[str]]) -> Optional[str]:
    """Return a reason string if the job should be pruned, else None."""
    if never_run_names and job.name in never_run_names:
        return "never executed (provided as never-run list)"
    if job.command.strip().lower() in ("", "true", "/bin/true", ":"):
        return "command is a no-op"
    if job.name.lower().startswith("disabled_") or job.name.lower().startswith("old_"):
        return "name suggests disabled or legacy job"
    return None


def prune_config(
    config: Config,
    never_run_names: Optional[List[str]] = None,
) -> PruneResult:
    pruned: List[PrunedJob] = []
    total = 0
    for server in config.servers:
        for job in server.jobs:
            total += 1
            reason = _should_prune(job, never_run_names)
            if reason:
                pruned.append(
                    PrunedJob(
                        server=server.name,
                        job_name=job.name,
                        schedule=job.schedule,
                        command=job.command,
                        reason=reason,
                    )
                )
    return PruneResult(pruned=pruned, total_scanned=total)
