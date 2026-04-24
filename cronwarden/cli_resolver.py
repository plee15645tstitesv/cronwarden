"""CLI entry point for the resolver command."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List

from cronwarden.config import ConfigError, load_config
from cronwarden.resolver import ResolveResult, resolve_config


def _parse_env_args(raw: List[str]) -> Dict[str, str]:
    env: Dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise ValueError(f"Invalid env format '{item}', expected KEY=VALUE")
        key, _, value = item.partition("=")
        env[key.strip()] = value.strip()
    return env


def _format_text(result: ResolveResult) -> str:
    lines = []
    for job in result.jobs:
        icon = "✓" if not job.unresolved_vars else "✗"
        lines.append(f"  {icon} [{job.server}] {job.job_name}")
        if job.original_command != job.resolved_command:
            lines.append(f"      original : {job.original_command}")
            lines.append(f"      resolved : {job.resolved_command}")
        if job.unresolved_vars:
            lines.append(f"      missing  : {', '.join(job.unresolved_vars)}")
    summary = (
        f"\nTotal: {result.total()} jobs, "
        f"{result.unresolved_count()} with unresolved variables."
    )
    return "\n".join(lines) + summary


def _format_json(result: ResolveResult) -> str:
    return json.dumps(
        [
            {
                "server": j.server,
                "job": j.job_name,
                "original": j.original_command,
                "resolved": j.resolved_command,
                "unresolved_vars": j.unresolved_vars,
            }
            for j in result.jobs
        ],
        indent=2,
    )


def run_resolver(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden resolve",
        description="Resolve environment variables in cron job commands.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--env",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help="Environment variable to substitute (repeatable)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        env = _parse_env_args(args.env)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = resolve_config(config, env)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    return 0
