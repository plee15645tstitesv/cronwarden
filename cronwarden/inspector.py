"""Inspector: deep-inspect a single cron job and produce a structured report."""

from dataclasses import dataclass, field
from typing import List, Optional

from cronwarden.config import CronJob, Server
from cronwarden.validator import validate_job
from cronwarden.linter import lint_job
from cronwarden.scorer import score_job
from cronwarden.explainer import explain_schedule
from cronwarden.classifier import _classify_job


@dataclass
class InspectionResult:
    server_name: str
    job_name: str
    schedule: str
    command: str
    description: Optional[str]
    tags: List[str]
    is_valid: bool
    validation_errors: List[str]
    lint_warnings: List[str]
    score: int
    grade: str
    schedule_explanation: str
    category: str

    def summary(self) -> str:
        status = "PASS" if self.is_valid else "FAIL"
        return (
            f"[{status}] {self.server_name}/{self.job_name} "
            f"score={self.score} ({self.grade}) category={self.category}"
        )


def inspect_job(server: Server, job: CronJob) -> InspectionResult:
    """Run all analysis passes on a single job and return an InspectionResult."""
    validation = validate_job(job)
    lint = lint_job(job)
    scored = score_job(server, job)
    explanation = explain_schedule(job.schedule)
    category = _classify_job(job)

    return InspectionResult(
        server_name=server.name,
        job_name=job.name,
        schedule=job.schedule,
        command=job.command,
        description=job.description,
        tags=list(job.tags) if job.tags else [],
        is_valid=validation.is_valid,
        validation_errors=[e for e in [validation.error] if e],
        lint_warnings=[str(w) for w in lint.warnings],
        score=scored.score,
        grade=scored.grade,
        schedule_explanation=explanation,
        category=category,
    )
