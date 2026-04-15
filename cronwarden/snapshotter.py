"""Snapshot management for cron job configurations.

Allows saving and loading config snapshots to disk for use with the differ.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cronwarden.config import Config, CronJob, Server

DEFAULT_SNAPSHOT_DIR = Path(".cronwarden_snapshots")


class SnapshotError(Exception):
    pass


def _config_to_dict(config: Config) -> dict:
    return {
        "servers": [
            {
                "name": server.name,
                "host": server.host,
                "jobs": [
                    {
                        "name": job.name,
                        "schedule": job.schedule,
                        "command": job.command,
                        "description": job.description,
                    }
                    for job in server.jobs
                ],
            }
            for server in config.servers
        ]
    }


def _dict_to_config(data: dict) -> Config:
    servers = []
    for s in data.get("servers", []):
        jobs = [
            CronJob(
                name=j["name"],
                schedule=j["schedule"],
                command=j["command"],
                description=j.get("description"),
            )
            for j in s.get("jobs", [])
        ]
        servers.append(Server(name=s["name"], host=s["host"], jobs=jobs))
    return Config(servers=servers)


def save_snapshot(
    config: Config,
    label: Optional[str] = None,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> Path:
    """Persist a config snapshot to disk. Returns the path of the saved file."""
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{label}_{timestamp}.json" if label else f"{timestamp}.json"
    path = snapshot_dir / filename
    payload = {"saved_at": timestamp, "config": _config_to_dict(config)}
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_snapshot(path: Path) -> Config:
    """Load a config snapshot from disk."""
    if not path.exists():
        raise SnapshotError(f"Snapshot file not found: {path}")
    try:
        data = json.loads(path.read_text())
        return _dict_to_config(data["config"])
    except (KeyError, ValueError) as exc:
        raise SnapshotError(f"Invalid snapshot file '{path}': {exc}") from exc


def list_snapshots(snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR) -> list[Path]:
    """Return snapshot paths sorted oldest-first."""
    if not snapshot_dir.exists():
        return []
    return sorted(snapshot_dir.glob("*.json"))
