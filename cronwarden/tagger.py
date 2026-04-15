"""Tag-based filtering for cron jobs."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config, CronJob, Server


@dataclass
class TagFilterResult:
    """Result of filtering a config by tags."""
    matched_servers: List[Server] = field(default_factory=list)
    total_jobs: int = 0
    matched_jobs: int = 0

    @property
    def has_matches(self) -> bool:
        return self.matched_jobs > 0


def _job_has_tag(job: CronJob, tag: str) -> bool:
    """Return True if the job has the given tag (case-insensitive)."""
    tags = getattr(job, "tags", None) or []
    return tag.lower() in [t.lower() for t in tags]


def filter_by_tag(config: Config, tag: str) -> TagFilterResult:
    """Filter config jobs by a single tag, returning a TagFilterResult."""
    result = TagFilterResult()

    for server in config.servers:
        result.total_jobs += len(server.jobs)
        matched = [job for job in server.jobs if _job_has_tag(job, tag)]
        if matched:
            filtered_server = Server(
                name=server.name,
                host=server.host,
                jobs=matched,
            )
            result.matched_servers.append(filtered_server)
            result.matched_jobs += len(matched)

    return result


def list_all_tags(config: Config) -> List[str]:
    """Return a sorted, deduplicated list of all tags across all jobs."""
    seen = set()
    for server in config.servers:
        for job in server.jobs:
            for tag in (getattr(job, "tags", None) or []):
                seen.add(tag.lower())
    return sorted(seen)
