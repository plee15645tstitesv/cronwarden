"""Sample random jobs from a config for spot-checking."""
from __future__ import annotations
import random
from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob, Server


@dataclass
class SampledJob:
    server: str
    job: CronJob

    def summary(self) -> str:
        return f"[{self.server}] {self.job.name} ({self.job.schedule})"


@dataclass
class SampleResult:
    samples: List[SampledJob] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.samples)

    @property
    def is_empty(self) -> bool:
        return self.total == 0

    def __str__(self) -> str:
        if self.is_empty:
            return "No jobs sampled."
        lines = [f"Sampled {self.total} job(s):"] + [f"  - {s.summary()}" for s in self.samples]
        return "\n".join(lines)


def sample_config(
    config: Config,
    n: int = 5,
    seed: Optional[int] = None,
    tag: Optional[str] = None,
) -> SampleResult:
    """Return up to *n* randomly chosen jobs from *config*."""
    rng = random.Random(seed)
    pool: List[SampledJob] = []
    for server in config.servers:
        for job in server.jobs:
            if tag is None or (job.tags and tag in job.tags):
                pool.append(SampledJob(server=server.name, job=job))
    chosen = rng.sample(pool, min(n, len(pool)))
    return SampleResult(samples=chosen)
