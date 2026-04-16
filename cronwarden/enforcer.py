from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob


@dataclass
class EnforcementViolation:
    server: str
    job_name: str
    rule: str
    detail: str

    def summary(self) -> str:
        return f"[{self.server}] {self.job_name}: {self.rule} — {self.detail}"


@dataclass
class EnforcementResult:
    violations: List[EnforcementViolation] = field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def total(self) -> int:
        return len(self.violations)

    def __str__(self) -> str:
        if not self.has_violations:
            return "All jobs comply with enforcement rules."
        lines = [f"{self.total} violation(s) found:"]
        for v in self.violations:
            lines.append(f"  - {v.summary()}")
        return "\n".join(lines)


def _check_required_tags(job: CronJob, server: str, required_tags: List[str]) -> Optional[EnforcementViolation]:
    job_tags = job.tags or []
    missing = [t for t in required_tags if t not in job_tags]
    if missing:
        return EnforcementViolation(
            server=server,
            job_name=job.name,
            rule="required-tags",
            detail=f"Missing required tag(s): {', '.join(missing)}",
        )
    return None


def _check_forbidden_commands(job: CronJob, server: str, forbidden: List[str]) -> Optional[EnforcementViolation]:
    for pattern in forbidden:
        if pattern in job.command:
            return EnforcementViolation(
                server=server,
                job_name=job.name,
                rule="forbidden-command",
                detail=f"Command contains forbidden pattern: '{pattern}'",
            )
    return None


def enforce(
    config: Config,
    required_tags: Optional[List[str]] = None,
    forbidden_commands: Optional[List[str]] = None,
) -> EnforcementResult:
    required_tags = required_tags or []
    forbidden_commands = forbidden_commands or []
    result = EnforcementResult()

    for server in config.servers:
        for job in server.jobs:
            if required_tags:
                v = _check_required_tags(job, server.name, required_tags)
                if v:
                    result.violations.append(v)
            if forbidden_commands:
                v = _check_forbidden_commands(job, server.name, forbidden_commands)
                if v:
                    result.violations.append(v)

    return result
