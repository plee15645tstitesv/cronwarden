from dataclasses import dataclass, field
from typing import List

from cronwarden.config import Config
from cronwarden.auditor import audit_config
from cronwarden.summarizer import summarize
from cronwarden.scorer import score_config
from cronwarden.linter import lint_config


@dataclass
class AuditSummaryReport:
    total_servers: int
    total_jobs: int
    valid_jobs: int
    invalid_jobs: int
    lint_warnings: int
    average_score: float
    health_percent: float
    top_issues: List[str] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return self.invalid_jobs == 0 and self.lint_warnings == 0

    def __str__(self) -> str:
        status = "HEALTHY" if self.is_healthy else "NEEDS ATTENTION"
        lines = [
            f"Audit Summary [{status}]",
            f"  Servers      : {self.total_servers}",
            f"  Total Jobs   : {self.total_jobs}",
            f"  Valid        : {self.valid_jobs}",
            f"  Invalid      : {self.invalid_jobs}",
            f"  Lint Warnings: {self.lint_warnings}",
            f"  Avg Score    : {self.average_score:.1f}",
            f"  Health       : {self.health_percent:.1f}%",
        ]
        if self.top_issues:
            lines.append("  Top Issues:")
            for issue in self.top_issues:
                lines.append(f"    - {issue}")
        return "\n".join(lines)


def build_audit_summary(config: Config) -> AuditSummaryReport:
    server_reports = audit_config(config)
    stats = summarize(config)
    score_result = score_config(config)

    valid_jobs = 0
    invalid_jobs = 0
    top_issues: List[str] = []

    for sr in server_reports:
        for jr in sr.job_reports:
            if jr.result.is_valid:
                valid_jobs += 1
            else:
                invalid_jobs += 1
                for err in jr.result.errors[:1]:
                    top_issues.append(f"{sr.server.name}/{jr.job.name}: {err}")

    lint_warnings = 0
    for server in config.servers:
        for job in server.jobs:
            lr = lint_config(config)
            lint_warnings = sum(len(r.warnings) for r in lr)
            break
        break

    # Re-compute lint properly
    lint_warnings = 0
    lr = lint_config(config)
    lint_warnings = sum(len(r.warnings) for r in lr)

    return AuditSummaryReport(
        total_servers=stats.total_servers,
        total_jobs=stats.total_jobs,
        valid_jobs=valid_jobs,
        invalid_jobs=invalid_jobs,
        lint_warnings=lint_warnings,
        average_score=score_result.average_score,
        health_percent=stats.health_percent,
        top_issues=top_issues[:5],
    )
