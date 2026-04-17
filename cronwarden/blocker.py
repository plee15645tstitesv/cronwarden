"""Blocker: detect cron jobs that overlap in schedule and command timing."""
from dataclasses import dataclass, field
from typing import List
from cronwarden.config import Config
from cronwarden.scheduler import next_run_for_job


@dataclass
class BlockedPair:
    server: str
    job_a: str
    job_b: str
    schedule_a: str
    schedule_b: str
    reason: str

    def summary(self) -> str:
        return f"[{self.server}] '{self.job_a}' and '{self.job_b}' may overlap: {self.reason}"


@dataclass
class BlockerResult:
    pairs: List[BlockedPair] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.pairs) > 0

    @property
    def total(self) -> int:
        return len(self.pairs)

    def __str__(self) -> str:
        if not self.has_conflicts:
            return "No overlapping jobs detected."
        lines = [p.summary() for p in self.pairs]
        return "\n".join(lines)


def _schedules_may_overlap(sched_a: str, sched_b: str) -> bool:
    """Heuristic: jobs with identical schedules may overlap."""
    return sched_a.strip() == sched_b.strip()


def find_conflicts(config: Config) -> BlockerResult:
    result = BlockerResult()
    for server in config.servers:
        jobs = server.jobs
        for i in range(len(jobs)):
            for j in range(i + 1, len(jobs)):
                a, b = jobs[i], jobs[j]
                if _schedules_may_overlap(a.schedule, b.schedule):
                    pair = BlockedPair(
                        server=server.name,
                        job_a=a.name,
                        job_b=b.name,
                        schedule_a=a.schedule,
                        schedule_b=b.schedule,
                        reason="identical schedule expression",
                    )
                    result.pairs.append(pair)
    return result
