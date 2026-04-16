"""Pin jobs to expected schedules and detect drift from pinned values."""

from dataclasses import dataclass, field
from typing import Optional
from cronwarden.config import Config, CronJob


@dataclass
class PinnedJob:
    server: str
    job_name: str
    expected_schedule: str
    actual_schedule: str

    @property
    def has_drifted(self) -> bool:
        return self.expected_schedule.strip() != self.actual_schedule.strip()

    def summary(self) -> str:
        if self.has_drifted:
            return (
                f"[DRIFT] {self.server}/{self.job_name}: "
                f"expected '{self.expected_schedule}', "
                f"got '{self.actual_schedule}'"
            )
        return f"[OK]    {self.server}/{self.job_name}: '{self.actual_schedule}'"


@dataclass
class PinResult:
    pins: list[PinnedJob] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return any(p.has_drifted for p in self.pins)

    @property
    def drifted(self) -> list[PinnedJob]:
        return [p for p in self.pins if p.has_drifted]

    @property
    def total(self) -> int:
        return len(self.pins)

    @property
    def drift_count(self) -> int:
        return len(self.drifted)


def check_pins(config: Config, pins: dict[str, dict[str, str]]) -> PinResult:
    """Compare pinned schedules against actual job schedules in config.

    Args:
        config: Loaded Config instance.
        pins: Mapping of {server_name: {job_name: expected_schedule}}.

    Returns:
        PinResult with a PinnedJob entry for every matched job.
    """
    result = PinResult()

    for server in config.servers:
        server_pins = pins.get(server.name, {})
        job_map: dict[str, CronJob] = {job.name: job for job in server.jobs}

        for job_name, expected_schedule in server_pins.items():
            actual_schedule = (
                job_map[job_name].schedule if job_name in job_map else "<missing>"
            )
            result.pins.append(
                PinnedJob(
                    server=server.name,
                    job_name=job_name,
                    expected_schedule=expected_schedule,
                    actual_schedule=actual_schedule,
                )
            )

    return result
