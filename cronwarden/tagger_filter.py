"""Filter and narrow config views by one or more tags."""
from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, Server, CronJob


@dataclass
class TagFilteredServer:
    server_name: str
    matched_jobs: List[CronJob]

    def summary(self) -> str:
        return f"{self.server_name}: {len(self.matched_jobs)} job(s) matched"


@dataclass
class TagFilteredResult:
    tags: List[str]
    servers: List[TagFilteredServer] = field(default_factory=list)

    @property
    def has_matches(self) -> bool:
        return any(s.matched_jobs for s in self.servers)

    @property
    def total_matched(self) -> int:
        return sum(len(s.matched_jobs) for s in self.servers)

    @property
    def matched_server_names(self) -> List[str]:
        return [s.server_name for s in self.servers if s.matched_jobs]


def _job_matches_any_tag(job: CronJob, tags: List[str]) -> bool:
    job_tags = [t.lower() for t in (job.tags or [])]
    return any(t.lower() in job_tags for t in tags)


def filter_config_by_tags(
    config: Config,
    tags: List[str],
    require_all: bool = False,
) -> TagFilteredResult:
    """Return a result containing only jobs that match the given tags.

    Args:
        config: The loaded Config object.
        tags: List of tag strings to filter by.
        require_all: If True, a job must have ALL listed tags to match.
    """
    result = TagFilteredResult(tags=tags)
    for server in config.servers:
        matched: List[CronJob] = []
        for job in server.jobs:
            job_tags = [t.lower() for t in (job.tags or [])]
            if require_all:
                if all(t.lower() in job_tags for t in tags):
                    matched.append(job)
            else:
                if any(t.lower() in job_tags for t in tags):
                    matched.append(job)
        result.servers.append(
            TagFilteredServer(server_name=server.name, matched_jobs=matched)
        )
    return result
