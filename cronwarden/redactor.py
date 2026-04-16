"""Redactor module: detect and mask sensitive values in cron job commands."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from cronwarden.config import Config

# Patterns that suggest a value is sensitive
_SENSITIVE_PATTERNS: list[re.Pattern] = [
    re.compile(r'(?i)(password|passwd|secret|token|api[_-]?key|auth)\s*=\s*\S+'),
    re.compile(r'(?i)--(password|token|secret|key)\s+\S+'),
    re.compile(r'(?i)(-p|--pass)\s+\S+'),
]

_MASK = "***REDACTED***"


@dataclass
class RedactedJob:
    server: str
    job_name: str
    original_command: str
    redacted_command: str
    was_redacted: bool

    @property
    def summary(self) -> str:
        flag = " [redacted]" if self.was_redacted else ""
        return f"{self.server}/{self.job_name}: {self.redacted_command}{flag}"


@dataclass
class RedactionResult:
    jobs: List[RedactedJob] = field(default_factory=list)

    @property
    def has_redactions(self) -> bool:
        return any(j.was_redacted for j in self.jobs)

    @property
    def total_redacted(self) -> int:
        return sum(1 for j in self.jobs if j.was_redacted)


def redact_command(command: str) -> tuple[str, bool]:
    """Return (redacted_command, was_changed) for a single command string."""
    result = command
    for pattern in _SENSITIVE_PATTERNS:
        result = pattern.sub(
            lambda m: re.sub(r'(=|\s)\S+$', lambda v: v.group(1) + _MASK, m.group()),
            result,
        )
    return result, result != command


def redact_config(config: Config) -> RedactionResult:
    """Scan all jobs in the config and redact sensitive command fragments."""
    result = RedactionResult()
    for server in config.servers:
        for job in server.jobs:
            redacted, changed = redact_command(job.command)
            result.jobs.append(
                RedactedJob(
                    server=server.name,
                    job_name=job.name,
                    original_command=job.command,
                    redacted_command=redacted,
                    was_redacted=changed,
                )
            )
    return result
