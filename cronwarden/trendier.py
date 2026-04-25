"""Trend analysis for cron job schedules across snapshot history."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.historian import SnapshotEntry


@dataclass
class TrendPoint:
    label: str
    total_jobs: int
    invalid_jobs: int
    server_count: int

    def summary(self) -> str:
        return (
            f"{self.label}: {self.total_jobs} jobs "
            f"({self.invalid_jobs} invalid) across {self.server_count} servers"
        )


@dataclass
class TrendResult:
    points: List[TrendPoint] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.points) == 0

    @property
    def total(self) -> int:
        return len(self.points)

    @property
    def growing(self) -> Optional[bool]:
        """Return True if total_jobs is increasing, False if decreasing, None if flat/unknown."""
        if len(self.points) < 2:
            return None
        first = self.points[0].total_jobs
        last = self.points[-1].total_jobs
        if last > first:
            return True
        if last < first:
            return False
        return None

    @property
    def peak_point(self) -> Optional[TrendPoint]:
        if not self.points:
            return None
        return max(self.points, key=lambda p: p.total_jobs)


def build_trend(entries: List[SnapshotEntry]) -> TrendResult:
    """Build a TrendResult from a list of SnapshotEntry objects."""
    points: List[TrendPoint] = []
    for entry in entries:
        config = entry.config
        total_jobs = sum(len(s.jobs) for s in config.servers)
        server_count = len(config.servers)
        # Count invalid jobs by checking schedule fields naively
        invalid = 0
        for server in config.servers:
            for job in server.jobs:
                parts = job.schedule.split()
                if len(parts) not in (5,) and not job.schedule.startswith("@"):
                    invalid += 1
        points.append(
            TrendPoint(
                label=entry.label or entry.filename,
                total_jobs=total_jobs,
                invalid_jobs=invalid,
                server_count=server_count,
            )
        )
    return TrendResult(points=points)
