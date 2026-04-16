"""Trace which jobs would be affected by a schedule or command pattern change."""
from dataclasses import dataclass, field
from typing import List
import re

from cronwarden.config import Config, CronJob, Server


@dataclass
class TraceMatch:
    server: str
    job: CronJob

    def summary(self) -> str:
        return f"[{self.server}] {self.job.name} — {self.job.schedule} — {self.job.command}"


@dataclass
class TraceResult:
    pattern: str
    field: str
    matches: List[TraceMatch] = field(default_factory=list)

    @property
    def has_matches(self) -> bool:
        return len(self.matches) > 0

    @property
    def total(self) -> int:
        return len(self.matches)

    def __str__(self) -> str:
        if not self.has_matches:
            return f"No jobs matched '{self.pattern}' in field '{self.field}'."
        lines = [f"{self.total} job(s) matched '{self.pattern}' in field '{self.field}':"]
        for m in self.matches:
            lines.append(f"  {m.summary()}")
        return "\n".join(lines)


def trace_jobs(config: Config, pattern: str, field: str = "command") -> TraceResult:
    """Find all jobs whose `field` matches the given regex pattern."""
    if field not in ("command", "schedule", "name"):
        raise ValueError(f"Unsupported trace field: '{field}'. Use 'command', 'schedule', or 'name'.")

    result = TraceResult(pattern=pattern, field=field)
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern '{pattern}': {exc}") from exc

    for server in config.servers:
        for job in server.jobs:
            value = getattr(job, field)
            if regex.search(value):
                result.matches.append(TraceMatch(server=server.name, job=job))

    return result
