"""CLI subcommand: cronwarden group — display jobs grouped by tag, server, or frequency."""

import sys
import json
import argparse
from cronwarden.config import load_config, ConfigError
from cronwarden.grouper import group_by_tag, group_by_server, group_by_frequency

_GROUPERS = {
    "tag": group_by_tag,
    "server": group_by_server,
    "frequency": group_by_frequency,
}


def _format_text(grouped) -> str:
    lines = [f"Grouped by: {grouped.dimension}\n"]
    for group_name in grouped.group_names():
        entries = grouped.jobs_in_group(group_name)
        lines.append(f"  [{group_name}] ({len(entries)} job(s))")
        for server, job in entries:
            desc = f" — {job.description}" if job.description else ""
            lines.append(f"    • {server.name} / {job.name}  {job.schedule}{desc}")
    lines.append(f"\nTotal: {grouped.total_jobs()} job(s) across {len(grouped.group_names())} group(s)")
    return "\n".join(lines)


def _format_json(grouped) -> str:
    data = {
        "dimension": grouped.dimension,
        "groups": {
            name: [
                {"server": s.name, "job": j.name, "schedule": j.schedule,
                 "description": j.description, "tags": j.tags}
                for s, j in grouped.jobs_in_group(name)
            ]
            for name in grouped.group_names()
        },
        "total_jobs": grouped.total_jobs(),
    }
    return json.dumps(data, indent=2)


def run_group(argv=None):
    parser = argparse.ArgumentParser(
        prog="cronwarden group",
        description="Group cron jobs by tag, server, or frequency.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--by",
        choices=list(_GROUPERS.keys()),
        default="tag",
        help="Dimension to group by (default: tag)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    grouped = _GROUPERS[args.by](config)

    if args.fmt == "json":
        print(_format_json(grouped))
    else:
        print(_format_text(grouped))

    sys.exit(0)
