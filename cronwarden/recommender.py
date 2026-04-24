from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob


@dataclass
class Recommendation:
    server: str
    job_name: str
    code: str
    message: str
    suggestion: str

    def summary(self) -> str:
        return f"[{self.code}] {self.server}/{self.job_name}: {self.message}"


@dataclass
class RecommendationResult:
    recommendations: List[Recommendation] = field(default_factory=list)

    @property
    def has_recommendations(self) -> bool:
        return len(self.recommendations) > 0

    @property
    def total(self) -> int:
        return len(self.recommendations)


def _check_job(server_name: str, job: CronJob) -> List[Recommendation]:
    results: List[Recommendation] = []

    if job.schedule == "* * * * *":
        results.append(Recommendation(
            server=server_name,
            job_name=job.name,
            code="R001",
            message="Job runs every minute which may cause resource contention.",
            suggestion="Consider using a less frequent schedule such as '*/5 * * * *'.",
        ))

    if job.command and "sudo" in job.command:
        results.append(Recommendation(
            server=server_name,
            job_name=job.name,
            code="R002",
            message="Command uses sudo; prefer running cron jobs as a dedicated user.",
            suggestion="Remove sudo and configure the cron to run as the appropriate user.",
        ))

    if not job.tags:
        results.append(Recommendation(
            server=server_name,
            job_name=job.name,
            code="R003",
            message="Job has no tags, making it harder to filter and group.",
            suggestion="Add at least one tag such as 'backup', 'cleanup', or 'monitoring'.",
        ))

    if not job.description:
        results.append(Recommendation(
            server=server_name,
            job_name=job.name,
            code="R004",
            message="Job has no description.",
            suggestion="Add a short description explaining what this job does.",
        ))

    return results


def recommend(config: Config) -> RecommendationResult:
    all_recs: List[Recommendation] = []
    for server in config.servers:
        for job in server.jobs:
            all_recs.extend(_check_job(server.name, job))
    return RecommendationResult(recommendations=all_recs)
