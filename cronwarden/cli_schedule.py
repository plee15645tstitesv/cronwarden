"""CLI sub-command: show next scheduled run times for all cron jobs."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import List

from cronwarden.config import ConfigError, load_config
from cronwarden.scheduler import NextRunResult, next_runs_for_config


def _format_text(results: List[NextRunResult]) -> str:
    lines = []
    for r in results:
        lines.append(str(r))
    return "\n".join(lines)


def _format_json(results: List[NextRunResult]) -> str:
    data = []
    for r in results:
        data.append({
            "server": r.server_name,
            "job": r.job_name,
            "schedule": r.schedule,
            "next_run": r.next_run.isoformat() if r.next_run else None,
            "error": r.error,
        })
    return json.dumps(data, indent=2)


def run_schedule(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden schedule",
        description="Show the next scheduled run time for each cron job.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--reference",
        metavar="DATETIME",
        help="Reference datetime for calculation (ISO format, default: now)",
    )
    args = parser.parse_args(argv)

    reference: datetime | None = None
    if args.reference:
        try:
            reference = datetime.fromisoformat(args.reference)
        except ValueError:
            print(f"Error: invalid --reference datetime: {args.reference!r}", file=sys.stderr)
            return 1

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 1

    results = next_runs_for_config(config, reference=reference)

    if not results:
        print("No jobs found.", file=sys.stderr)
        return 0

    if args.fmt == "json":
        print(_format_json(results))
    else:
        print(_format_text(results))

    errors = [r for r in results if not r.is_ok]
    return 1 if errors else 0
