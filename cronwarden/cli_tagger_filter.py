"""CLI entry point for the tag-filter command."""
import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.tagger_filter import filter_config_by_tags


def _format_text(result) -> str:
    lines = [f"Tag filter: {', '.join(result.tags)}"]
    lines.append(f"Total matched: {result.total_matched}")
    lines.append("")
    for server in result.servers:
        if not server.matched_jobs:
            continue
        lines.append(f"  [{server.server_name}]")
        for job in server.matched_jobs:
            tags_str = ", ".join(job.tags or [])
            lines.append(f"    - {job.name} ({job.schedule}) [{tags_str}]")
    return "\n".join(lines)


def _format_json(result) -> str:
    data = {
        "tags": result.tags,
        "total_matched": result.total_matched,
        "servers": [
            {
                "server": s.server_name,
                "matched_jobs": [
                    {
                        "name": j.name,
                        "schedule": j.schedule,
                        "command": j.command,
                        "tags": j.tags or [],
                    }
                    for j in s.matched_jobs
                ],
            }
            for s in result.servers
            if s.matched_jobs
        ],
    }
    return json.dumps(data, indent=2)


def run_tag_filter(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden tag-filter",
        description="Filter cron jobs by tag(s).",
    )
    parser.add_argument("config", help="Path to config file")
    parser.add_argument("tags", nargs="+", help="Tag(s) to filter by")
    parser.add_argument(
        "--all",
        dest="require_all",
        action="store_true",
        help="Require ALL tags to match (default: any)",
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

    result = filter_config_by_tags(config, args.tags, require_all=args.require_all)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    return 0
