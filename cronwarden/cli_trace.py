"""CLI entry point for the trace command."""
import argparse
import json
import sys

from cronwarden.config import load_config, ConfigError
from cronwarden.tracer import trace_jobs


def _format_text(result) -> str:
    return str(result)


def _format_json(result) -> str:
    data = {
        "pattern": result.pattern,
        "field": result.field,
        "total": result.total,
        "matches": [
            {
                "server": m.server,
                "job": m.job.name,
                "schedule": m.job.schedule,
                "command": m.job.command,
            }
            for m in result.matches
        ],
    }
    return json.dumps(data, indent=2)


def run_trace(argv=None):
    parser = argparse.ArgumentParser(
        prog="cronwarden trace",
        description="Trace which cron jobs match a pattern.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument("pattern", help="Regex pattern to search for")
    parser.add_argument(
        "--field",
        choices=["command", "schedule", "name"],
        default="command",
        help="Job field to match against (default: command)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        result = trace_jobs(config, args.pattern, field=args.field)
    except ValueError as exc:
        print(f"Trace error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    sys.exit(0)
