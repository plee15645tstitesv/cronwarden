"""Score cron jobs based on quality/health metrics."""
from dataclasses import dataclass, field
from typing import List
from cronwarden.config import Config, CronJob, Server
from cronwarden.validator import validate_job
from cronwarden.linter import lint_job


@dataclass
class JobScore:
    server_name: str
    job_name: str
    score: int  # 0-100
    reasons: List[str] = field(default_factory=list)

    def grade(self) -> str:
        if self.score >= 90:
            return "A"
        elif self.score >= 75:
            return "B"
        elif self.score >= 60:
            return "C"
        elif self.score >= 40:
            return "D"
        return "F"

    def summary(self) -> str:
        return f"{self.server_name}/{self.job_name}: {self.score}/100 ({self.grade()})"


@dataclass
class ScoreResult:
    scores: List[JobScore] = field(default_factory=list)

    def average_score(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(s.score for s in self.scores) / len(self.scores), 1)

    def lowest(self) -> JobScore | None:
        if not self.scores:
            return None
        return min(self.scores, key=lambda s: s.score)

    def highest(self) -> JobScore | None:
        if not self.scores:
            return None
        return max(self.scores, key=lambda s: s.score)

    def is_healthy(self) -> bool:
        return self.average_score() >= 75.0


def _score_job(server: Server, job: CronJob) -> JobScore:
    score = 100
    reasons = []

    result = validate_job(job)
    if not result.is_valid:
        score -= 40
        reasons.append(f"validation failed: {'; '.join(result.errors)}")

    lint_result = lint_job(job)
    if not lint_result.is_clean():
        deduction = len(lint_result.warnings) * 10
        score -= min(deduction, 30)
        for w in lint_result.warnings:
            reasons.append(str(w))

    if not job.tags:
        score -= 5
        reasons.append("no tags assigned")

    if not job.description:
        score -= 5
        reasons.append("no description provided")

    score = max(0, score)
    return JobScore(server_name=server.name, job_name=job.name, score=score, reasons=reasons)


def score_config(config: Config) -> ScoreResult:
    scores = []
    for server in config.servers:
        for job in server.jobs:
            scores.append(_score_job(server, job))
    return ScoreResult(scores=scores)
