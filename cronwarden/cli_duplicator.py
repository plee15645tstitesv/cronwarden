"""CLI entry point for the duplicate job detection command."""

import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.duplicator import find_duplicates


def _format_text(result) -> str:
    return str(result)


def _format_json(result) -> str:
    data = [
        {
            "schedule": g.schedule,
            "command": g.command,
            "occurrences": [
                {"server": s.name, "job": j.name}
                for s, j in g.jobs
            ],
        }
        for g in result.groups
    ]
    return json.dumps({"duplicates": data}, indent=2)


def run_duplicates(argv=None):
    import argparse

    parser = argparse.ArgumentParser(
        prog="cronwarden duplicates",
        description="Detect duplicate cron jobs across servers.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-duplicates",
        action="store_true",
        help="Exit with code 1 if duplicates are found",
    )

    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)

    result = find_duplicates(config)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    if args.fail_on_duplicates and result.has_duplicates:
        sys.exit(1)

    sys.exit(0)
