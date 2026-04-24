"""Resolve environment variables and placeholders in cron job commands."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwarden.config import Config, CronJob, Server


@dataclass
class ResolvedJob:
    server: str
    job_name: str
    original_command: str
    resolved_command: str
    unresolved_vars: List[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.unresolved_vars:
            return f"{self.server}/{self.job_name}: unresolved {self.unresolved_vars}"
        return f"{self.server}/{self.job_name}: fully resolved"


@dataclass
class ResolveResult:
    jobs: List[ResolvedJob] = field(default_factory=list)

    def has_unresolved(self) -> bool:
        return any(j.unresolved_vars for j in self.jobs)

    def total(self) -> int:
        return len(self.jobs)

    def is_empty(self) -> bool:
        return len(self.jobs) == 0

    def unresolved_count(self) -> int:
        return sum(1 for j in self.jobs if j.unresolved_vars)


_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}|\$([A-Z_][A-Z0-9_]*)")


def _find_vars(command: str) -> List[str]:
    return [
        m.group(1) or m.group(2)
        for m in _VAR_PATTERN.finditer(command)
    ]


def _resolve_command(command: str, env: Dict[str, str]) -> tuple[str, List[str]]:
    unresolved: List[str] = []

    def replacer(m: re.Match) -> str:
        var = m.group(1) or m.group(2)
        if var in env:
            return env[var]
        unresolved.append(var)
        return m.group(0)

    resolved = _VAR_PATTERN.sub(replacer, command)
    return resolved, unresolved


def resolve_config(
    config: Config,
    env: Optional[Dict[str, str]] = None,
) -> ResolveResult:
    """Resolve environment variable placeholders in all job commands."""
    env = env or {}
    result = ResolveResult()

    for server in config.servers:
        for job in server.jobs:
            resolved_cmd, unresolved = _resolve_command(job.command, env)
            result.jobs.append(
                ResolvedJob(
                    server=server.name,
                    job_name=job.name,
                    original_command=job.command,
                    resolved_command=resolved_cmd,
                    unresolved_vars=unresolved,
                )
            )

    return result
