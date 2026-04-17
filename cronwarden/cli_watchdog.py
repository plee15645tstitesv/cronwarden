"""CLI entry point for the watchdog command."""
import argparse
import json
import sys
from datetime import datetime
from cronwarden.config import load_config, ConfigError
from cronwarden.watchdog import check_watchdog


def _parse_last_seen(raw: list) -> dict:
    """Parse 'server:job:ISO8601' strings into a {(server, job): datetime} map."""
    result = {}
    for entry in raw or []:
        parts = entry.split(":", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid last-seen entry: {entry!r} (expected server:job:datetime)")
        server, job, ts = parts
        result[(server, job)] = datetime.fromisoformat(ts)
    return result


def _format_text(result) -> str:
    return str(result)


def _format_json(result) -> str:
    data = [
        {
            "server": o.server,
            "job": o.job.name,
            "expected_by": o.expected_by.isoformat(),
            "last_seen": o.last_seen.isoformat() if o.last_seen else None,
            "summary": o.summary(),
        }
        for o in result.overdue
    ]
    return json.dumps({"overdue": data, "total": result.total}, indent=2)


def run_watchdog(argv=None):
    parser = argparse.ArgumentParser(description="Detect overdue cron jobs")
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--last-seen",
        nargs="*",
        metavar="SERVER:JOB:DATETIME",
        help="Last seen timestamps per job",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument(
        "--fail-on-overdue",
        action="store_true",
        help="Exit with code 1 if any jobs are overdue",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        last_seen_map = _parse_last_seen(args.last_seen)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    result = check_watchdog(config, last_seen_map)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    if args.fail_on_overdue and result.has_overdue:
        sys.exit(1)
    sys.exit(0)
