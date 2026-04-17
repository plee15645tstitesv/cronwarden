"""CLI command: flatten — list all cron jobs across servers in a flat view."""
import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.flattener import flatten_config


def _format_text(result) -> str:
    if result.is_empty:
        return "No jobs found."
    lines = []
    for job in result.jobs:
        lines.append(job.summary())
    lines.append(f"\nTotal: {result.total} job(s)")
    return "\n".join(lines)


def _format_json(result) -> str:
    data = [
        {
            "server": j.server,
            "name": j.name,
            "schedule": j.schedule,
            "command": j.command,
            "description": j.description,
            "tags": j.tags,
        }
        for j in result.jobs
    ]
    return json.dumps(data, indent=2)


def run_flatten(argv=None):
    parser = argparse.ArgumentParser(description="Flatten all cron jobs into a single list.")
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--tag", default=None, help="Filter jobs by tag")
    parser.add_argument("--server", default=None, help="Filter jobs by server name")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = flatten_config(config)

    if args.tag:
        result.jobs = result.with_tag(args.tag)
    if args.server:
        result.jobs = result.for_server(args.server)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    sys.exit(0)
