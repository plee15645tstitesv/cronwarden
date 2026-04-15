"""Schedule next-run calculator for cron jobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

try:
    from croniter import croniter
except ImportError:  # pragma: no cover
    croniter = None  # type: ignore

from cronwarden.config import Config, CronJob


@dataclass
class NextRunResult:
    server_name: str
    job_name: str
    schedule: str
    next_run: Optional[datetime]
    error: Optional[str] = None

    @property
    def is_ok(self) -> bool:
        return self.error is None

    def __str__(self) -> str:
        if self.error:
            return f"{self.server_name}/{self.job_name}: ERROR — {self.error}"
        ts = self.next_run.strftime("%Y-%m-%d %H:%M") if self.next_run else "unknown"
        return f"{self.server_name}/{self.job_name}: next run at {ts} (schedule: {self.schedule})"


def next_run_for_job(
    job: CronJob,
    server_name: str,
    reference: Optional[datetime] = None,
) -> NextRunResult:
    """Return the next scheduled run time for a single job."""
    if croniter is None:
        return NextRunResult(
            server_name=server_name,
            job_name=job.name,
            schedule=job.schedule,
            next_run=None,
            error="croniter is not installed",
        )

    base = reference or datetime.now()

    # Handle special @-syntax aliases
    schedule = job.schedule
    _aliases = {
        "@yearly": "0 0 1 1 *",
        "@annually": "0 0 1 1 *",
        "@monthly": "0 0 1 * *",
        "@weekly": "0 0 * * 0",
        "@daily": "0 0 * * *",
        "@midnight": "0 0 * * *",
        "@hourly": "0 * * * *",
    }
    schedule = _aliases.get(schedule, schedule)

    try:
        itr = croniter(schedule, base)
        nxt: datetime = itr.get_next(datetime)
        return NextRunResult(
            server_name=server_name,
            job_name=job.name,
            schedule=job.schedule,
            next_run=nxt,
        )
    except Exception as exc:  # noqa: BLE001
        return NextRunResult(
            server_name=server_name,
            job_name=job.name,
            schedule=job.schedule,
            next_run=None,
            error=str(exc),
        )


def next_runs_for_config(
    config: Config,
    reference: Optional[datetime] = None,
) -> List[NextRunResult]:
    """Return next-run results for every job across all servers."""
    results: List[NextRunResult] = []
    for server in config.servers:
        for job in server.jobs:
            results.append(next_run_for_job(job, server.name, reference))
    return results
