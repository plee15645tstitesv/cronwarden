"""Cron expression validator for cronwarden."""

import re
from dataclasses import dataclass
from typing import Optional

from cronwarden.config import CronJob

CRON_FIELD_RANGES = [
    ("minute", 0, 59),
    ("hour", 0, 23),
    ("day_of_month", 1, 31),
    ("month", 1, 12),
    ("day_of_week", 0, 7),
]

SPECIAL_STRINGS = {
    "@reboot", "@yearly", "@annually", "@monthly",
    "@weekly", "@daily", "@midnight", "@hourly",
}


@dataclass
class ValidationResult:
    job_name: str
    schedule: str
    valid: bool
    error: Optional[str] = None

    def __str__(self) -> str:
        if self.valid:
            return f"[OK]  {self.job_name}: '{self.schedule}'"
        return f"[ERR] {self.job_name}: '{self.schedule}' — {self.error}"


def _validate_field(value: str, min_val: int, max_val: int) -> bool:
    """Validate a single cron field against its allowed range."""
    if value == "*":
        return True

    # Step values like */5 or 1-5/2
    if "/" in value:
        parts = value.split("/", 1)
        if not parts[1].isdigit():
            return False
        step = int(parts[1])
        if step < 1:
            return False
        value = parts[0]
        if value == "*":
            return True

    # Range like 1-5
    if "-" in value:
        parts = value.split("-", 1)
        if not (parts[0].isdigit() and parts[1].isdigit()):
            return False
        lo, hi = int(parts[0]), int(parts[1])
        return min_val <= lo <= hi <= max_val

    # List like 1,2,3
    if "," in value:
        return all(_validate_field(v, min_val, max_val) for v in value.split(","))

    # Plain integer
    if value.isdigit():
        return min_val <= int(value) <= max_val

    return False


def validate_schedule(schedule: str) -> Optional[str]:
    """Return an error message if the schedule is invalid, else None."""
    schedule = schedule.strip()

    if schedule in SPECIAL_STRINGS:
        return None

    fields = schedule.split()
    if len(fields) != 5:
        return f"expected 5 fields, got {len(fields)}"

    for field_value, (field_name, min_val, max_val) in zip(fields, CRON_FIELD_RANGES):
        if not _validate_field(field_value, min_val, max_val):
            return f"invalid value '{field_value}' for field '{field_name}' (range {min_val}-{max_val})"

    return None


def validate_job(job: CronJob) -> ValidationResult:
    """Validate a single CronJob's schedule expression."""
    error = validate_schedule(job.schedule)
    return ValidationResult(
        job_name=job.name,
        schedule=job.schedule,
        valid=error is None,
        error=error,
    )


def validate_jobs(jobs: list[CronJob]) -> list[ValidationResult]:
    """Validate a list of CronJob objects and return their results."""
    return [validate_job(job) for job in jobs]
