"""Generates a summary report for tag usage across all cron jobs in a config."""

from dataclasses import dataclass, field
from typing import Dict, List

from cronwarden.config import Config
from cronwarden.tagger import list_all_tags, filter_by_tag


@dataclass
class TagStat:
    tag: str
    job_count: int
    servers: List[str]

    def summary(self) -> str:
        servers_str = ", ".join(sorted(self.servers))
        return f"[{self.tag}] {self.job_count} job(s) on: {servers_str}"


@dataclass
class TagReportResult:
    stats: List[TagStat] = field(default_factory=list)
    total_tags: int = 0
    total_tagged_jobs: int = 0
    untagged_job_count: int = 0

    def is_empty(self) -> bool:
        return self.total_tags == 0

    def most_used_tag(self) -> str | None:
        if not self.stats:
            return None
        return max(self.stats, key=lambda s: s.job_count).tag

    def __str__(self) -> str:
        lines = [f"Tag Report: {self.total_tags} tag(s), {self.total_tagged_jobs} tagged job(s), {self.untagged_job_count} untagged"]
        for stat in sorted(self.stats, key=lambda s: -s.job_count):
            lines.append(f"  {stat.summary()}")
        return "\n".join(lines)


def build_tag_report(config: Config) -> TagReportResult:
    all_tags = list_all_tags(config)
    stats: List[TagStat] = []
    tagged_job_names = set()

    for tag in all_tags:
        result = filter_by_tag(config, tag)
        servers_with_tag = []
        count = 0
        for server_name, jobs in result.matches.items():
            count += len(jobs)
            if jobs:
                servers_with_tag.append(server_name)
                for job in jobs:
                    tagged_job_names.add((server_name, job.name))
        stats.append(TagStat(tag=tag, job_count=count, servers=servers_with_tag))

    untagged = 0
    for server in config.servers:
        for job in server.jobs:
            if not job.tags:
                untagged += 1

    return TagReportResult(
        stats=stats,
        total_tags=len(all_tags),
        total_tagged_jobs=len(tagged_job_names),
        untagged_job_count=untagged,
    )
