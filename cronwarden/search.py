"""Search/filter cron jobs by keyword across name, command, and description."""

from dataclasses import dataclass, field
from typing import List, Tuple

from cronwarden.config import Config, CronJob, Server


@dataclass
class SearchMatch:
    server: Server
    job: CronJob
    matched_fields: List[str] = field(default_factory=list)

    def summary(self) -> str:
        fields = ", ".join(self.matched_fields)
        return f"[{self.server.name}] {self.job.name} (matched: {fields})"


@dataclass
class SearchResult:
    query: str
    matches: List[SearchMatch] = field(default_factory=list)

    @property
    def has_matches(self) -> bool:
        return len(self.matches) > 0

    @property
    def total(self) -> int:
        return len(self.matches)


def _job_matches(
    job: CronJob, query: str
) -> Tuple[bool, List[str]]:
    """Return (matched, list_of_matched_field_names) for a job and query."""
    q = query.lower()
    matched_fields: List[str] = []

    if q in job.name.lower():
        matched_fields.append("name")
    if q in job.command.lower():
        matched_fields.append("command")
    if job.description and q in job.description.lower():
        matched_fields.append("description")
    if any(q in tag.lower() for tag in (job.tags or [])):
        matched_fields.append("tags")

    return bool(matched_fields), matched_fields


def search_config(config: Config, query: str) -> SearchResult:
    """Search all jobs in a config for jobs matching the query string."""
    result = SearchResult(query=query)

    for server in config.servers:
        for job in server.jobs:
            matched, fields = _job_matches(job, query)
            if matched:
                result.matches.append(
                    SearchMatch(server=server, job=job, matched_fields=fields)
                )

    return result
