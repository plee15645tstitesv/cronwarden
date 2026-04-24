"""Digest module: produce a concise daily/weekly summary digest of all cron jobs."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config
from cronwarden.validator import validate_job
from cronwarden.estimator import estimate_config


@dataclass
class DigestEntry:
    server: str
    job_name: str
    schedule: str
    command: str
    runs_per_day: float
    is_valid: bool
    description: Optional[str] = None

    def summary(self) -> str:
        status = "OK" if self.is_valid else "INVALID"
        return (
            f"[{status}] {self.server}/{self.job_name} "
            f"({self.schedule}) ~{self.runs_per_day:.1f}x/day"
        )


@dataclass
class DigestResult:
    entries: List[DigestEntry] = field(default_factory=list)
    total_servers: int = 0
    total_jobs: int = 0
    invalid_count: int = 0

    @property
    def is_empty(self) -> bool:
        return len(self.entries) == 0

    @property
    def has_invalid(self) -> bool:
        return self.invalid_count > 0

    def __str__(self) -> str:
        lines = [
            f"Digest: {self.total_jobs} jobs across {self.total_servers} server(s), "
            f"{self.invalid_count} invalid"
        ]
        for entry in self.entries:
            lines.append(f"  {entry.summary()}")
        return "\n".join(lines)


def build_digest(config: Config) -> DigestResult:
    """Build a digest of all cron jobs from a config."""
    estimation = estimate_config(config)
    estimates_by_key = {
        (e.server, e.job_name): e for e in estimation.estimates
    }

    entries: List[DigestEntry] = []
    invalid_count = 0

    for server in config.servers:
        for job in server.jobs:
            result = validate_job(job)
            is_valid = result.is_valid
            if not is_valid:
                invalid_count += 1

            key = (server.name, job.name)
            est = estimates_by_key.get(key)
            runs_per_day = est.runs_per_day if est else 0.0

            entries.append(DigestEntry(
                server=server.name,
                job_name=job.name,
                schedule=job.schedule,
                command=job.command,
                runs_per_day=runs_per_day,
                is_valid=is_valid,
                description=job.description,
            ))

    return DigestResult(
        entries=entries,
        total_servers=len(config.servers),
        total_jobs=len(entries),
        invalid_count=invalid_count,
    )
