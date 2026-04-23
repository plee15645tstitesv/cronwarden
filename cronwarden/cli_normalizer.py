"""CLI entry point for the normalizer command."""

import argparse
import json
import sys

from cronwarden.config import load_config, ConfigError
from cronwarden.normalizer import normalize_config


def _format_text(result) -> str:
    lines = []
    lines.append(f"Normalized {result.total} job(s), {result.total_changed} changed.")
    if result.has_changes:
        lines.append("")
        lines.append("Changes:")
        for job in result.changed_jobs():
            lines.append(f"  {job.summary()}")
    return "\n".join(lines)


def _format_json(result) -> str:
    data = {
        "total": result.total,
        "total_changed": result.total_changed,
        "has_changes": result.has_changes,
        "jobs": [
            {
                "server": j.server,
                "job_name": j.job_name,
                "original_schedule": j.original_schedule,
                "normalized_schedule": j.normalized_schedule,
                "was_changed": j.was_changed,
            }
            for j in result.jobs
        ],
    }
    return json.dumps(data, indent=2)


def run_normalize(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden normalize",
        description="Normalize cron job schedules to canonical form.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Only report jobs whose schedule was changed",
    )

    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = normalize_config(config)

    if args.changed_only and not result.has_changes:
        if args.format == "json":
            print(json.dumps({"total_changed": 0, "jobs": []}))
        else:
            print("No schedule normalization changes detected.")
        return 0

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    return 0
