"""Fingerprinter: generate stable hashes for cron jobs to detect identity changes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List

from cronwarden.config import Config, CronJob


def _job_fingerprint(server_name: str, job: CronJob) -> str:
    """Return a stable SHA-256 fingerprint for a job based on its identity fields."""
    raw = f"{server_name}|{job.name}|{job.schedule}|{job.command}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class FingerprintEntry:
    server: str
    job_name: str
    schedule: str
    command: str
    fingerprint: str

    def summary(self) -> str:
        return f"[{self.server}] {self.job_name} -> {self.fingerprint}"


@dataclass
class FingerprintResult:
    entries: List[FingerprintEntry]

    @property
    def is_empty(self) -> bool:
        return len(self.entries) == 0

    @property
    def total(self) -> int:
        return len(self.entries)

    def get_fingerprint(self, server: str, job_name: str) -> str | None:
        """Look up the fingerprint for a specific server/job pair."""
        for entry in self.entries:
            if entry.server == server and entry.job_name == job_name:
                return entry.fingerprint
        return None

    def as_dict(self) -> dict:
        return {
            e.fingerprint: {"server": e.server, "job": e.job_name}
            for e in self.entries
        }


def fingerprint_config(config: Config) -> FingerprintResult:
    """Generate fingerprints for all jobs in a config."""
    entries: List[FingerprintEntry] = []
    for server in config.servers:
        for job in server.jobs:
            fp = _job_fingerprint(server.name, job)
            entries.append(
                FingerprintEntry(
                    server=server.name,
                    job_name=job.name,
                    schedule=job.schedule,
                    command=job.command,
                    fingerprint=fp,
                )
            )
    return FingerprintResult(entries=entries)
