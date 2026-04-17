"""Detect jobs that may depend on each other based on shared resources or naming patterns."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob


@dataclass
class JobDependency:
    server: str
    job_name: str
    depends_on_name: str
    reason: str

    def summary(self) -> str:
        return f"{self.server}/{self.job_name} -> {self.depends_on_name} ({self.reason})"


@dataclass
class DependencyResult:
    dependencies: List[JobDependency] = field(default_factory=list)

    @property
    def has_dependencies(self) -> bool:
        return len(self.dependencies) > 0

    @property
    def total(self) -> int:
        return len(self.dependencies)


def _extract_tokens(text: str) -> set:
    import re
    return set(re.findall(r'[\w]+', text.lower()))


STOP_WORDS = {"the", "a", "and", "or", "to", "in", "of", "for", "on", "at", "job", "run", "cron"}


def _significant_tokens(text: str) -> set:
    return _extract_tokens(text) - STOP_WORDS


def find_dependencies(config: Config, min_overlap: int = 2) -> DependencyResult:
    """Find jobs that likely depend on each other based on name/command token overlap."""
    result = DependencyResult()

    all_jobs: List[tuple] = []
    for server in config.servers:
        for job in server.jobs:
            all_jobs.append((server.name, job))

    for i, (srv_a, job_a) in enumerate(all_jobs):
        tokens_a = _significant_tokens(f"{job_a.name} {job_a.command}")
        for j, (srv_b, job_b) in enumerate(all_jobs):
            if i >= j:
                continue
            tokens_b = _significant_tokens(f"{job_b.name} {job_b.command}")
            overlap = tokens_a & tokens_b
            if len(overlap) >= min_overlap:
                result.dependencies.append(JobDependency(
                    server=srv_a,
                    job_name=job_a.name,
                    depends_on_name=job_b.name,
                    reason=f"shared tokens: {', '.join(sorted(overlap))}",
                ))

    return result
