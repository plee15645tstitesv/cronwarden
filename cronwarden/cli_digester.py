"""CLI entry point for the digest command."""

import argparse
import json
import sys

from cronwarden.config import load_config, ConfigError
from cronwarden.digester import build_digest, DigestResult


def _format_text(result: DigestResult) -> str:
    lines = [
        f"=== CronWarden Digest ===",
        f"Servers : {result.total_servers}",
        f"Jobs    : {result.total_jobs}",
        f"Invalid : {result.invalid_count}",
        "",
    ]
    for entry in result.entries:
        status = "✓" if entry.is_valid else "✗"
        desc = f" — {entry.description}" if entry.description else ""
        lines.append(
            f"  {status} [{entry.server}] {entry.job_name}{desc}"
        )
        lines.append(
            f"      schedule: {entry.schedule}  "
            f"cmd: {entry.command}  "
            f"~{entry.runs_per_day:.1f}x/day"
        )
    return "\n".join(lines)


def _format_json(result: DigestResult) -> str:
    data = {
        "total_servers": result.total_servers,
        "total_jobs": result.total_jobs,
        "invalid_count": result.invalid_count,
        "entries": [
            {
                "server": e.server,
                "job_name": e.job_name,
                "schedule": e.schedule,
                "command": e.command,
                "runs_per_day": e.runs_per_day,
                "is_valid": e.is_valid,
                "description": e.description,
            }
            for e in result.entries
        ],
    }
    return json.dumps(data, indent=2)


def run_digest(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden digest",
        description="Produce a concise digest of all cron jobs.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--fail-on-invalid", action="store_true",
        help="Exit with code 1 if any jobs are invalid"
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = build_digest(config)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    if args.fail_on_invalid and result.has_invalid:
        return 1
    return 0
