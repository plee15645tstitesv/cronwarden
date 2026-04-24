"""Heatmap: build a frequency map of cron job execution times across hours/days."""

from dataclasses import dataclass, field
from typing import Dict, List

from cronwarden.config import Config


@dataclass
class HeatmapCell:
    hour: int
    dow: int  # 0=Sunday, 6=Saturday; -1 means wildcard/all
    count: int

    def summary(self) -> str:
        day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        day = day_names[self.dow] if self.dow >= 0 else "All"
        hour_str = f"{self.hour:02d}:xx" if self.hour >= 0 else "All"
        return f"{day} {hour_str} -> {self.count} job(s)"


@dataclass
class HeatmapResult:
    cells: List[HeatmapCell] = field(default_factory=list)
    total_jobs: int = 0

    def is_empty(self) -> bool:
        return len(self.cells) == 0

    def peak_cell(self) -> HeatmapCell | None:
        if not self.cells:
            return None
        return max(self.cells, key=lambda c: c.count)

    def to_dict(self) -> Dict:
        return {
            "total_jobs": self.total_jobs,
            "cells": [
                {"hour": c.hour, "dow": c.dow, "count": c.count}
                for c in self.cells
            ],
        }


def _parse_field(value: str) -> List[int]:
    """Return list of concrete values from a cron field, or [-1] for wildcard."""
    if value == "*":
        return [-1]
    if "," in value:
        parts = []
        for part in value.split(","):
            parts.extend(_parse_field(part.strip()))
        return parts
    if "/" in value:
        return [-1]  # step values treated as wildcard for heatmap purposes
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


def build_heatmap(config: Config) -> HeatmapResult:
    """Build a heatmap of job execution frequency by hour and day-of-week."""
    counts: Dict[tuple, int] = {}
    total = 0

    for server in config.servers:
        for job in server.jobs:
            total += 1
            schedule = job.schedule.strip()

            # Skip special @-style schedules
            if schedule.startswith("@"):
                key = (-1, -1)
                counts[key] = counts.get(key, 0) + 1
                continue

            parts = schedule.split()
            if len(parts) != 5:
                continue

            _minute, hour_field, _dom, _month, dow_field = parts
            hours = _parse_field(hour_field)
            dows = _parse_field(dow_field)

            for h in hours:
                for d in dows:
                    key = (h, d)
                    counts[key] = counts.get(key, 0) + 1

    cells = [
        HeatmapCell(hour=h, dow=d, count=c)
        for (h, d), c in sorted(counts.items())
    ]
    return HeatmapResult(cells=cells, total_jobs=total)
