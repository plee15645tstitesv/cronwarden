"""Segment cron jobs into time-based buckets (hourly, daily, weekly, monthly, other)."""

from dataclasses import dataclass, field
from typing import Dict, List
from cronwarden.config import Config, CronJob


SEGMENT_LABELS = ["hourly", "daily", "weekly", "monthly", "other"]


@dataclass
class SegmentEntry:
    server: str
    job_name: str
    schedule: str
    segment: str

    def summary(self) -> str:
        return f"[{self.segment}] {self.server}/{self.job_name} ({self.schedule})"


@dataclass
class SegmentResult:
    buckets: Dict[str, List[SegmentEntry]] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return self.total == 0

    @property
    def total(self) -> int:
        return sum(len(v) for v in self.buckets.values())

    def jobs_in_segment(self, segment: str) -> List[SegmentEntry]:
        return self.buckets.get(segment, [])

    def segment_counts(self) -> Dict[str, int]:
        return {seg: len(entries) for seg, entries in self.buckets.items()}


def _classify_schedule(schedule: str) -> str:
    """Return a segment label based on the cron schedule string."""
    special_map = {
        "@hourly": "hourly",
        "@daily": "daily",
        "@midnight": "daily",
        "@weekly": "weekly",
        "@monthly": "monthly",
        "@yearly": "other",
        "@annually": "other",
        "@reboot": "other",
    }
    if schedule in special_map:
        return special_map[schedule]

    parts = schedule.split()
    if len(parts) != 5:
        return "other"

    minute, hour, dom, month, dow = parts

    if minute == "*" and hour == "*":
        return "hourly"
    if dom == "*" and month == "*" and dow == "*":
        return "daily"
    if dow != "*" and dom == "*":
        return "weekly"
    if dom != "*" and month == "*":
        return "monthly"
    return "other"


def segment_config(config: Config) -> SegmentResult:
    """Segment all jobs in the config into time-based buckets."""
    buckets: Dict[str, List[SegmentEntry]] = {label: [] for label in SEGMENT_LABELS}

    for server in config.servers:
        for job in server.jobs:
            seg = _classify_schedule(job.schedule)
            entry = SegmentEntry(
                server=server.name,
                job_name=job.name,
                schedule=job.schedule,
                segment=seg,
            )
            buckets[seg].append(entry)

    return SegmentResult(buckets=buckets)
