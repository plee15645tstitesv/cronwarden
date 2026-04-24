"""CLI entry point for the mirror command."""
import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.mirrorer import mirror_jobs, MirrorResult


def _format_text(result: MirrorResult) -> str:
    if not result.has_mirrored:
        return (
            f"No jobs mirrored from '{result.source_server}' to '{result.target_server}'."
        )
    lines = [
        f"Mirrored {result.total} job(s) from '{result.source_server}' to '{result.target_server}':"
    ]
    for m in result.mirrored:
        lines.append(f"  - {m.summary()}")
    return "\n".join(lines)


def _format_json(result: MirrorResult) -> str:
    data = {
        "source_server": result.source_server,
        "target_server": result.target_server,
        "total": result.total,
        "mirrored": [
            {
                "job_name": m.job_name,
                "schedule": m.schedule,
                "command": m.command,
            }
            for m in result.mirrored
        ],
    }
    return json.dumps(data, indent=2)


def run_mirror(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Mirror cron jobs from one server to another."
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument("--from", dest="source", required=True, help="Source server name")
    parser.add_argument("--to", dest="target", required=True, help="Target server name")
    parser.add_argument("--filter", dest="name_filter", default=None, help="Filter jobs by name substring")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        result = mirror_jobs(config, args.source, args.target, name_filter=args.name_filter)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    return 0
