"""Lint cron jobs for common issues beyond basic validation."""

from dataclasses import dataclass, field
from typing import List
from cronwarden.config import CronJob


@dataclass
class LintWarning:
    job_name: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"[{self.code}] {self.job_name}: {self.message}"


@dataclass
class LintResult:
    job_name: str
    warnings: List[LintWarning] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return len(self.warnings) == 0


def _check_no_description(job: CronJob) -> List[LintWarning]:
    warnings = []
    if not job.description:
        warnings.append(LintWarning(
            job_name=job.name,
            code="W001",
            message="Job has no description; consider documenting its purpose."
        ))
    return warnings


def _check_root_command(job: CronJob) -> List[LintWarning]:
    warnings = []
    cmd = job.command.strip()
    if cmd.startswith("sudo ") or "sudo" in cmd.split():
        warnings.append(LintWarning(
            job_name=job.name,
            code="W002",
            message="Command uses sudo; verify this is intentional and secure."
        ))
    return warnings


def _check_no_output_redirect(job: CronJob) -> List[LintWarning]:
    warnings = []
    cmd = job.command
    if ">>" not in cmd and ">" not in cmd and "2>&1" not in cmd:
        warnings.append(LintWarning(
            job_name=job.name,
            code="W003",
            message="Command has no output redirection; output may be lost or emailed."
        ))
    return warnings


def _check_every_minute(job: CronJob) -> List[LintWarning]:
    warnings = []
    parts = job.schedule.strip().split()
    if len(parts) == 5 and parts[0] == "*" and parts[1] == "*":
        warnings.append(LintWarning(
            job_name=job.name,
            code="W004",
            message="Job runs every minute; confirm high frequency is intended."
        ))
    return warnings


LINT_CHECKS = [
    _check_no_description,
    _check_root_command,
    _check_no_output_redirect,
    _check_every_minute,
]


def lint_job(job: CronJob) -> LintResult:
    result = LintResult(job_name=job.name)
    for check in LINT_CHECKS:
        result.warnings.extend(check(job))
    return result


def lint_all(jobs: List[CronJob]) -> List[LintResult]:
    return [lint_job(job) for job in jobs]
