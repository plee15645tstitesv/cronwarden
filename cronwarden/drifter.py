"""Detect schedule drift: jobs whose schedules have changed since a baseline snapshot."""
from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config
from cronwarden.snapshotter import load_snapshot


@dataclass
class DriftedJob:
    server: str
    job_name: str
    baseline_schedule: str
    current_schedule: str

    def summary(self) -> str:
        return (
            f"{self.server}/{self.job_name}: "
            f"{self.baseline_schedule!r} -> {self.current_schedule!r}"
        )


@dataclass
class DriftResult:
    drifted: List[DriftedJob] = field(default_factory=list)
    missing_in_baseline: List[str] = field(default_factory=list)
    missing_in_current: List[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(self.drifted)

    @property
    def total(self) -> int:
        return len(self.drifted)


def detect_drift(current: Config, snapshot_path: str) -> DriftResult:
    """Compare current config against a saved snapshot and report schedule drift."""
    baseline = load_snapshot(snapshot_path)
    result = DriftResult()

    baseline_index = {
        (srv.name, job.name): job.schedule
        for srv in baseline.servers
        for job in srv.jobs
    }
    current_index = {
        (srv.name, job.name): job.schedule
        for srv in current.servers
        for job in srv.jobs
    }

    for key, current_schedule in current_index.items():
        if key not in baseline_index:
            result.missing_in_baseline.append(f"{key[0]}/{key[1]}")
        elif baseline_index[key] != current_schedule:
            result.drifted.append(
                DriftedJob(
                    server=key[0],
                    job_name=key[1],
                    baseline_schedule=baseline_index[key],
                    current_schedule=current_schedule,
                )
            )

    for key in baseline_index:
        if key not in current_index:
            result.missing_in_current.append(f"{key[0]}/{key[1]}")

    return result
