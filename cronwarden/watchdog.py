"""Watchdog: detect jobs that haven't run within their expected window."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
from cronwarden.config import Config, CronJob, Server
from cronwarden.scheduler import next_run_for_job


@dataclass
class OverdueJob:
    server: str
    job: CronJob
    expected_by: datetime
    last_seen: Optional[datetime]

    def summary(self) -> str:
        last = self.last_seen.isoformat() if self.last_seen else "never"
        return (
            f"[{self.server}] {self.job.name} overdue since "
            f"{self.expected_by.isoformat()} (last seen: {last})"
        )


@dataclass
class WatchdogResult:
    overdue: List[OverdueJob] = field(default_factory=list)

    @property
    def has_overdue(self) -> bool:
        return len(self.overdue) > 0

    @property
    def total(self) -> int:
        return len(self.overdue)

    def __str__(self) -> str:
        if not self.has_overdue:
            return "All jobs are on schedule."
        lines = [f"{self.total} overdue job(s):"]
        for o in self.overdue:
            lines.append(f"  - {o.summary()}")
        return "\n".join(lines)


def check_watchdog(
    config: Config,
    last_seen_map: dict,
    reference_time: Optional[datetime] = None,
) -> WatchdogResult:
    """Check which jobs are overdue given a map of {(server, job_name): datetime}."""
    now = reference_time or datetime.utcnow()
    result = WatchdogResult()

    for server in config.servers:
        for job in server.jobs:
            key = (server.name, job.name)
            last_seen: Optional[datetime] = last_seen_map.get(key)
            next_result = next_run_for_job(job, reference_time=now)
            if next_result.error:
                continue
            # Estimate expected window: if last_seen is known, next run after last_seen
            if last_seen is not None:
                next_after_last = next_run_for_job(job, reference_time=last_seen)
                if next_after_last.error:
                    continue
                expected_by = next_after_last.next_run
                if expected_by and expected_by < now:
                    result.overdue.append(
                        OverdueJob(
                            server=server.name,
                            job=job,
                            expected_by=expected_by,
                            last_seen=last_seen,
                        )
                    )
            else:
                # Never seen — flag if schedule should have run within last 24h
                window_start = now - timedelta(hours=24)
                nr = next_run_for_job(job, reference_time=window_start)
                if nr.error:
                    continue
                if nr.next_run and nr.next_run < now:
                    result.overdue.append(
                        OverdueJob(
                            server=server.name,
                            job=job,
                            expected_by=nr.next_run,
                            last_seen=None,
                        )
                    )
    return result
