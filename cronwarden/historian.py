"""Historian: query and summarize snapshot history for a config."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from cronwarden.snapshotter import load_snapshot, list_snapshots
from cronwarden.config import Config


@dataclass
class SnapshotEntry:
    filename: str
    timestamp: datetime
    label: Optional[str]
    server_count: int
    job_count: int

    def summary(self) -> str:
        label_part = f" [{self.label}]" if self.label else ""
        return (
            f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}{label_part} "
            f"— {self.server_count} server(s), {self.job_count} job(s)"
        )


@dataclass
class HistoryResult:
    entries: List[SnapshotEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def latest(self) -> Optional[SnapshotEntry]:
        return self.entries[0] if self.entries else None

    def oldest(self) -> Optional[SnapshotEntry]:
        return self.entries[-1] if self.entries else None


def _count_jobs(config: Config) -> int:
    return sum(len(s.jobs) for s in config.servers)


def load_history(snapshot_dir: str) -> HistoryResult:
    """Load all snapshots from *snapshot_dir* and return a HistoryResult."""
    filenames = list_snapshots(snapshot_dir)
    entries: List[SnapshotEntry] = []

    for filename in filenames:
        path = os.path.join(snapshot_dir, filename)
        try:
            config, meta = load_snapshot(path)
        except Exception:
            continue

        ts = datetime.fromisoformat(meta.get("timestamp", "1970-01-01T00:00:00"))
        label = meta.get("label") or None
        entries.append(
            SnapshotEntry(
                filename=filename,
                timestamp=ts,
                label=label,
                server_count=len(config.servers),
                job_count=_count_jobs(config),
            )
        )

    # newest first
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return HistoryResult(entries=entries)
