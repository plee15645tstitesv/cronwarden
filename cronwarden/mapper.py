"""Maps cron jobs to a structured dependency/ownership matrix by server and schedule slot."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from cronwarden.config import Config, CronJob


@dataclass
class MapEntry:
    server: str
    job_name: str
    schedule: str
    command: str
    tags: List[str] = field(default_factory=list)

    def summary(self) -> str:
        tag_str = ", ".join(self.tags) if self.tags else "(none)"
        return f"[{self.server}] {self.job_name} | {self.schedule} | tags: {tag_str}"


@dataclass
class MapResult:
    entries: List[MapEntry] = field(default_factory=list)
    index: Dict[str, List[MapEntry]] = field(default_factory=dict)  # keyed by server

    @property
    def is_empty(self) -> bool:
        return len(self.entries) == 0

    @property
    def total(self) -> int:
        return len(self.entries)

    def servers(self) -> List[str]:
        return list(self.index.keys())

    def jobs_for_server(self, server: str) -> List[MapEntry]:
        return self.index.get(server, [])


def map_config(config: Config, tag: Optional[str] = None) -> MapResult:
    """Build a MapResult from a Config, optionally filtering by tag."""
    entries: List[MapEntry] = []
    index: Dict[str, List[MapEntry]] = {}

    for server in config.servers:
        server_entries: List[MapEntry] = []
        for job in server.jobs:
            job_tags = job.tags if job.tags else []
            if tag is not None and tag not in job_tags:
                continue
            entry = MapEntry(
                server=server.name,
                job_name=job.name,
                schedule=job.schedule,
                command=job.command,
                tags=job_tags,
            )
            entries.append(entry)
            server_entries.append(entry)
        if server_entries:
            index[server.name] = server_entries

    return MapResult(entries=entries, index=index)
