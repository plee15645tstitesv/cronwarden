"""balancer.py — Detect load imbalances across cron job schedules.

Analyses the distribution of jobs across hours and days to identify
times when too many jobs are scheduled to run simultaneously, which
could overwhelm system resources.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Tuple

from cronwarden.config import Config


# Number of jobs in the same slot that triggers an imbalance warning
DEFAULT_THRESHOLD = 3


@dataclass
class ImbalanceEntry:
    """Represents a single time slot that contains too many concurrent jobs."""

    hour: int          # 0-23, or -1 for wildcard
    minute: int        # 0-59, or -1 for wildcard
    job_count: int
    job_names: List[str]
    server_names: List[str]

    def summary(self) -> str:
        hour_str = "*" if self.hour == -1 else f"{self.hour:02d}"
        minute_str = "*" if self.minute == -1 else f"{self.minute:02d}"
        return (
            f"{hour_str}:{minute_str} — {self.job_count} concurrent jobs "
            f"({', '.join(self.job_names[:3])}{'...' if len(self.job_names) > 3 else ''})"
        )


@dataclass
class BalanceResult:
    """Result of a load-balance analysis over a Config."""

    imbalances: List[ImbalanceEntry] = field(default_factory=list)
    total_jobs: int = 0
    threshold: int = DEFAULT_THRESHOLD

    @property
    def has_imbalances(self) -> bool:
        return len(self.imbalances) > 0

    @property
    def total(self) -> int:
        return len(self.imbalances)

    def is_empty(self) -> bool:
        return self.total_jobs == 0


def _parse_field(value: str) -> List[int]:
    """Parse a single cron field into a list of concrete integer values.

    Handles wildcards (*), lists (1,2,3), and step values (*/5).
    Returns [-1] for pure wildcards to indicate "every unit".
    """
    value = value.strip()
    if value == "*":
        return [-1]
    if "/" in value and value.startswith("*"):
        # e.g. */15 — treat as wildcard for bucketing purposes
        return [-1]
    if "," in value:
        result = []
        for part in value.split(","):
            result.extend(_parse_field(part.strip()))
        return result
    if "-" in value:
        start, end = value.split("-", 1)
        try:
            return list(range(int(start), int(end) + 1))
        except ValueError:
            return [-1]
    try:
        return [int(value)]
    except ValueError:
        return [-1]


def check_balance(config: Config, threshold: int = DEFAULT_THRESHOLD) -> BalanceResult:
    """Analyse job schedules and flag time slots with too many concurrent jobs.

    Args:
        config:    Parsed Config containing servers and their jobs.
        threshold: Minimum number of jobs in the same slot to flag as an
                   imbalance. Defaults to DEFAULT_THRESHOLD.

    Returns:
        A BalanceResult with all detected imbalances.
    """
    # slot -> list of (job_name, server_name)
    slot_map: Dict[Tuple[int, int], List[Tuple[str, str]]] = {}

    total_jobs = 0
    for server in config.servers:
        for job in server.jobs:
            total_jobs += 1
            parts = job.schedule.split()
            if len(parts) < 5:
                continue

            minutes = _parse_field(parts[0])
            hours = _parse_field(parts[1])

            for h in hours:
                for m in minutes:
                    slot = (h, m)
                    slot_map.setdefault(slot, []).append((job.name, server.name))

    imbalances: List[ImbalanceEntry] = []
    for (hour, minute), entries in sorted(slot_map.items()):
        if len(entries) >= threshold:
            job_names = [e[0] for e in entries]
            server_names = list(dict.fromkeys(e[1] for e in entries))  # unique, ordered
            imbalances.append(
                ImbalanceEntry(
                    hour=hour,
                    minute=minute,
                    job_count=len(entries),
                    job_names=job_names,
                    server_names=server_names,
                )
            )

    return BalanceResult(
        imbalances=imbalances,
        total_jobs=total_jobs,
        threshold=threshold,
    )
