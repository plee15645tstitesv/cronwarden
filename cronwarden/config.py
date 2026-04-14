"""Config loader and validator for cronwarden.

Expects a YAML config file with the following structure:

  servers:
    - name: web-01
      host: web-01.example.com
      user: deploy
      jobs:
        - name: daily-backup
          schedule: "0 2 * * *"
          command: /usr/local/bin/backup.sh
          description: Nightly database backup
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class CronJob:
    name: str
    schedule: str
    command: str
    description: Optional[str] = None


@dataclass
class Server:
    name: str
    host: str
    user: str
    jobs: List[CronJob] = field(default_factory=list)


@dataclass
class Config:
    servers: List[Server] = field(default_factory=list)


class ConfigError(Exception):
    """Raised when the config file is missing or malformed."""


def load_config(path: str) -> Config:
    """Load and parse a cronwarden YAML config file.

    Args:
        path: Filesystem path to the YAML config file.

    Returns:
        A populated Config dataclass.

    Raises:
        ConfigError: If the file is missing, unreadable, or structurally invalid.
    """
    if not os.path.exists(path):
        raise ConfigError(f"Config file not found: {path}")

    with open(path, "r") as fh:
        try:
            raw = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ConfigError(f"Failed to parse YAML: {exc}") from exc

    if not isinstance(raw, dict) or "servers" not in raw:
        raise ConfigError("Config must contain a top-level 'servers' key.")

    servers: List[Server] = []
    for idx, srv in enumerate(raw["servers"]):
        for required in ("name", "host", "user"):
            if required not in srv:
                raise ConfigError(
                    f"Server at index {idx} is missing required field '{required}'."
                )
        jobs: List[CronJob] = []
        for jdx, job in enumerate(srv.get("jobs", [])):
            for required in ("name", "schedule", "command"):
                if required not in job:
                    raise ConfigError(
                        f"Job at index {jdx} on server '{srv['name']}' "
                        f"is missing required field '{required}'."
                    )
            jobs.append(
                CronJob(
                    name=job["name"],
                    schedule=job["schedule"],
                    command=job["command"],
                    description=job.get("description"),
                )
            )
        servers.append(
            Server(name=srv["name"], host=srv["host"], user=srv["user"], jobs=jobs)
        )

    return Config(servers=servers)
