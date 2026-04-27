from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob


@dataclass
class RankedJob:
    rank: int
    server: str
    job: CronJob
    score: float
    reason: str

    def summary(self) -> str:
        return f"#{self.rank} [{self.server}] {self.job.name} (score={self.score:.1f}) — {self.reason}"


@dataclass
class RankResult:
    entries: List[RankedJob] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def total(self) -> int:
        return len(self.entries)

    def top(self, n: int = 5) -> List[RankedJob]:
        return self.entries[:n]


def _score_job(job: CronJob) -> tuple[float, str]:
    score = 100.0
    reasons = []

    if not job.description:
        score -= 20.0
        reasons.append("no description")

    if not job.tags:
        score -= 10.0
        reasons.append("no tags")

    if job.command.startswith("sudo"):
        score -= 15.0
        reasons.append("uses sudo")

    if job.schedule == "* * * * *":
        score -= 25.0
        reasons.append("runs every minute")

    if any(kw in job.command.lower() for kw in ("password", "token", "secret")):
        score -= 30.0
        reasons.append("possible secret in command")

    reason = ", ".join(reasons) if reasons else "well configured"
    return max(score, 0.0), reason


def rank_config(
    config: Config,
    ascending: bool = False,
    limit: Optional[int] = None,
) -> RankResult:
    scored: List[tuple[float, str, str, CronJob]] = []

    for server in config.servers:
        for job in server.jobs:
            score, reason = _score_job(job)
            scored.append((score, reason, server.name, job))

    scored.sort(key=lambda x: x[0], reverse=not ascending)

    if limit is not None:
        scored = scored[:limit]

    entries = [
        RankedJob(rank=i + 1, server=srv, job=job, score=sc, reason=rsn)
        for i, (sc, rsn, srv, job) in enumerate(scored)
    ]

    return RankResult(entries=entries)
