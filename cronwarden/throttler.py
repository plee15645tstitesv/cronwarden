"""Throttler: detect cron jobs that run too frequently and may overload a system."""

from dataclasses import dataclass, field
from typing import List, Optional

from cronwarden.config import Config
from cronwarden.estimator import estimate_config


@dataclass
class ThrottledJob:
    server: str
    job_name: str
    schedule: str
    runs_per_day: float
    threshold: float
    command: str

    def summary(self) -> str:
        return (
            f"[{self.server}] {self.job_name!r} runs ~{self.runs_per_day:.1f}x/day "
            f"(threshold: {self.threshold:.1f})"
        )


@dataclass
class ThrottleResult:
    throttled: List[ThrottledJob] = field(default_factory=list)
    total_checked: int = 0

    @property
    def has_throttled(self) -> bool:
        return len(self.throttled) > 0

    @property
    def total(self) -> int:
        return len(self.throttled)


def check_throttle(
    config: Config,
    max_runs_per_day: float = 96.0,
    tag: Optional[str] = None,
) -> ThrottleResult:
    """Flag jobs that exceed max_runs_per_day.

    Args:
        config: Parsed cronwarden Config.
        max_runs_per_day: Maximum allowed runs per day before flagging (default 96 = every 15 min).
        tag: If provided, only check jobs with this tag.

    Returns:
        ThrottleResult with all offending jobs.
    """
    estimation = estimate_config(config)
    result = ThrottleResult(total_checked=estimation.total)

    for estimate in estimation.estimates:
        if tag and (not estimate.tags or tag not in estimate.tags):
            continue
        if estimate.runs_per_day > max_runs_per_day:
            result.throttled.append(
                ThrottledJob(
                    server=estimate.server,
                    job_name=estimate.job_name,
                    schedule=estimate.schedule,
                    runs_per_day=estimate.runs_per_day,
                    threshold=max_runs_per_day,
                    command=estimate.command,
                )
            )

    return result
