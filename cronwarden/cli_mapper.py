"""CLI entry point for the mapper feature."""

import argparse
import json
import sys

from cronwarden.config import load_config, ConfigError
from cronwarden.mapper import map_config, MapResult


def _format_text(result: MapResult, verbose: bool = False) -> str:
    if result.is_empty:
        return "No jobs found."
    lines = []
    for server in result.servers():
        lines.append(f"Server: {server}")
        for entry in result.jobs_for_server(server):
            lines.append(f"  {entry.summary()}")
            if verbose:
                lines.append(f"    command: {entry.command}")
    lines.append(f"\nTotal: {result.total} job(s) across {len(result.servers())} server(s)")
    return "\n".join(lines)


def _format_json(result: MapResult) -> str:
    data = {
        "total": result.total,
        "servers": [
            {
                "server": server,
                "jobs": [
                    {
                        "name": e.job_name,
                        "schedule": e.schedule,
                        "command": e.command,
                        "tags": e.tags,
                    }
                    for e in result.jobs_for_server(server)
                ],
            }
            for server in result.servers()
        ],
    }
    return json.dumps(data, indent=2)


def run_map(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Map cron jobs by server and schedule.")
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument("--tag", default=None, help="Filter by tag")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--verbose", action="store_true", help="Show full command")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = map_config(config, tag=args.tag)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result, verbose=args.verbose))

    return 0
