"""Group cron jobs by tag, server, or schedule frequency."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from cronwarden.config import Config, CronJob, Server


@dataclass
class GroupedJobs:
    """Result of grouping jobs by a given dimension."""
    dimension: str  # 'tag', 'server', or 'frequency'
    groups: Dict[str, List[Tuple[Server, CronJob]]] = field(default_factory=dict)

    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    def jobs_in_group(self, name: str) -> List[Tuple[Server, CronJob]]:
        return self.groups.get(name, [])

    def total_jobs(self) -> int:
        return sum(len(v) for v in self.groups.values())

    def is_empty(self) -> bool:
        return self.total_jobs() == 0


def _frequency_label(schedule: str) -> str:
    """Return a human-readable frequency bucket for a cron schedule."""
    special = {
        "@yearly": "yearly",
        "@annually": "yearly",
        "@monthly": "monthly",
        "@weekly": "weekly",
        "@daily": "daily",
        "@midnight": "daily",
        "@hourly": "hourly",
        "@reboot": "reboot",
    }
    if schedule in special:
        return special[schedule]

    parts = schedule.split()
    if len(parts) != 5:
        return "unknown"

    minute, hour, dom, month, dow = parts
    if minute == "*" and hour == "*":
        return "every-minute"
    if hour == "*":
        return "hourly"
    if dom == "*" and month == "*" and dow == "*":
        return "daily"
    if dow != "*":
        return "weekly"
    if dom != "*":
        return "monthly"
    return "other"


def group_by_tag(config: Config) -> GroupedJobs:
    """Group all jobs by their tags. Untagged jobs go under 'untagged'."""
    result: Dict[str, List[Tuple[Server, CronJob]]] = {}
    for server in config.servers:
        for job in server.jobs:
            tags = job.tags if job.tags else ["untagged"]
            for tag in tags:
                result.setdefault(tag, []).append((server, job))
    return GroupedJobs(dimension="tag", groups=result)


def group_by_server(config: Config) -> GroupedJobs:
    """Group all jobs by their server name."""
    result: Dict[str, List[Tuple[Server, CronJob]]] = {}
    for server in config.servers:
        for job in server.jobs:
            result.setdefault(server.name, []).append((server, job))
    return GroupedJobs(dimension="server", groups=result)


def group_by_frequency(config: Config) -> GroupedJobs:
    """Group all jobs by their schedule frequency bucket."""
    result: Dict[str, List[Tuple[Server, CronJob]]] = {}
    for server in config.servers:
        for job in server.jobs:
            label = _frequency_label(job.schedule)
            result.setdefault(label, []).append((server, job))
    return GroupedJobs(dimension="frequency", groups=result)
