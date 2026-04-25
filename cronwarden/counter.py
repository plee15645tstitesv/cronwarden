from dataclasses import dataclass, field
from typing import Dict, List
from cronwarden.config import Config


@dataclass
class CountEntry:
    server: str
    total_jobs: int
    by_schedule: Dict[str, int]
    by_user: Dict[str, int]

    def summary(self) -> str:
        return f"{self.server}: {self.total_jobs} job(s)"


@dataclass
class CountResult:
    entries: List[CountEntry] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.entries) == 0

    @property
    def total(self) -> int:
        return sum(e.total_jobs for e in self.entries)

    @property
    def total_servers(self) -> int:
        return len(self.entries)

    def grand_total_by_schedule(self) -> Dict[str, int]:
        combined: Dict[str, int] = {}
        for entry in self.entries:
            for schedule, count in entry.by_schedule.items():
                combined[schedule] = combined.get(schedule, 0) + count
        return combined


def count_config(config: Config) -> CountResult:
    entries: List[CountEntry] = []

    for server in config.servers:
        by_schedule: Dict[str, int] = {}
        by_user: Dict[str, int] = {}

        for job in server.jobs:
            schedule = job.schedule
            by_schedule[schedule] = by_schedule.get(schedule, 0) + 1

            user = (job.user or "unknown").strip()
            by_user[user] = by_user.get(user, 0) + 1

        entries.append(
            CountEntry(
                server=server.name,
                total_jobs=len(server.jobs),
                by_schedule=by_schedule,
                by_user=by_user,
            )
        )

    return CountResult(entries=entries)
