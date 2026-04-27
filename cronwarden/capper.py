"""capper.py — Detect jobs that exceed a maximum run-frequency cap.

A job is considered "over-capped" when its estimated runs-per-day exceeds
the supplied threshold (default: 96 runs/day, i.e. every 15 minutes).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from cronwarden.config import Config
from cronwarden.estimator import estimate_config


@dataclass
class CappedJob:
    server: str
    job_name: str
    schedule: str
    runs_per_day: float
    cap: float

    def summary(self) -> str:
        return (
            f"{self.server}/{self.job_name}: {self.runs_per_day:.1f} runs/day "
            f"(cap={self.cap:.1f})"
        )


@dataclass
class CapResult:
    capped: List[CappedJob] = field(default_factory=list)

    @property
    def has_capped(self) -> bool:
        return len(self.capped) > 0

    @property
    def total(self) -> int:
        return len(self.capped)

    def summary(self) -> str:
        if not self.has_capped:
            return "No over-capped jobs detected."
        lines = [f"Over-capped jobs ({self.total}):"]
        for c in self.capped:
            lines.append(f"  - {c.summary()}")
        return "\n".join(lines)


def check_cap(config: Config, cap: float = 96.0) -> CapResult:
    """Return a CapResult listing every job whose runs-per-day exceeds *cap*."""
    estimation = estimate_config(config)
    result = CapResult()
    for estimate in estimation.estimates:
        if estimate.runs_per_day > cap:
            result.capped.append(
                CappedJob(
                    server=estimate.server,
                    job_name=estimate.job_name,
                    schedule=estimate.schedule,
                    runs_per_day=estimate.runs_per_day,
                    cap=cap,
                )
            )
    return result
