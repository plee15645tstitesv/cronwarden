"""Scope analysis: identify jobs that target overlapping or redundant resource paths."""
from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob, Server


@dataclass
class ScopedJob:
    server: str
    job_name: str
    command: str
    scope: str  # extracted resource path/token
    overlap_with: List[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.overlap_with:
            return f"{self.server}/{self.job_name} [{self.scope}] overlaps with: {', '.join(self.overlap_with)}"
        return f"{self.server}/{self.job_name} [{self.scope}]"


@dataclass
class ScopeResult:
    entries: List[ScopedJob] = field(default_factory=list)

    @property
    def has_overlaps(self) -> bool:
        return any(e.overlap_with for e in self.entries)

    @property
    def total(self) -> int:
        return len(self.entries)

    @property
    def is_empty(self) -> bool:
        return self.total == 0

    def overlapping_entries(self) -> List[ScopedJob]:
        return [e for e in self.entries if e.overlap_with]


def _extract_scope(command: str) -> Optional[str]:
    """Extract a representative scope token from a command (path or keyword)."""
    tokens = command.split()
    for token in tokens:
        if token.startswith("/") and len(token) > 1:
            return token
    # Fall back to first non-flag argument
    for token in tokens:
        if not token.startswith("-") and token != tokens[0]:
            return token
    return tokens[0] if tokens else None


def analyze_scope(config: Config) -> ScopeResult:
    """Analyze all jobs and flag those sharing the same extracted scope token."""
    entries: List[ScopedJob] = []

    for server in config.servers:
        for job in server.jobs:
            scope = _extract_scope(job.command) or ""
            entries.append(ScopedJob(
                server=server.name,
                job_name=job.name,
                command=job.command,
                scope=scope,
            ))

    # Detect overlaps: jobs sharing the same non-trivial scope token
    scope_index: dict = {}
    for entry in entries:
        if not entry.scope:
            continue
        key = entry.scope
        scope_index.setdefault(key, []).append(entry)

    for scope_key, group in scope_index.items():
        if len(group) > 1:
            for entry in group:
                others = [
                    f"{e.server}/{e.job_name}"
                    for e in group
                    if e is not entry
                ]
                entry.overlap_with = others

    return ScopeResult(entries=entries)
