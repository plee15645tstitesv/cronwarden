from dataclasses import dataclass, field
from typing import List, Dict
from cronwarden.config import Config


@dataclass
class TagUsageStat:
    tag: str
    job_count: int
    server_count: int
    servers: List[str]

    def summary(self) -> str:
        return f"{self.tag}: {self.job_count} job(s) across {self.server_count} server(s)"


@dataclass
class TagStatsResult:
    stats: List[TagUsageStat] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.stats) == 0

    def total_tags(self) -> int:
        return len(self.stats)

    def most_used(self) -> TagUsageStat | None:
        if not self.stats:
            return None
        return max(self.stats, key=lambda s: s.job_count)

    def least_used(self) -> TagUsageStat | None:
        if not self.stats:
            return None
        return min(self.stats, key=lambda s: s.job_count)

    def tags_used_on_multiple_servers(self) -> List[TagUsageStat]:
        return [s for s in self.stats if s.server_count > 1]


def compute_tag_stats(config: Config) -> TagStatsResult:
    tag_jobs: Dict[str, int] = {}
    tag_servers: Dict[str, set] = {}

    for server in config.servers:
        for job in server.jobs:
            tags = job.tags or []
            for tag in tags:
                tag_jobs[tag] = tag_jobs.get(tag, 0) + 1
                if tag not in tag_servers:
                    tag_servers[tag] = set()
                tag_servers[tag].add(server.name)

    stats = [
        TagUsageStat(
            tag=tag,
            job_count=count,
            server_count=len(tag_servers[tag]),
            servers=sorted(tag_servers[tag]),
        )
        for tag, count in sorted(tag_jobs.items())
    ]

    return TagStatsResult(stats=stats)
