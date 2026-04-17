"""CLI entry point for the blocker (overlap detection) feature."""
import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.blocker import find_conflicts


def _format_text(result) -> str:
    return str(result)


def _format_json(result) -> str:
    data = {
        "has_conflicts": result.has_conflicts,
        "total": result.total,
        "pairs": [
            {
                "server": p.server,
                "job_a": p.job_a,
                "job_b": p.job_b,
                "schedule_a": p.schedule_a,
                "schedule_b": p.schedule_b,
                "reason": p.reason,
            }
            for p in result.pairs
        ],
    }
    return json.dumps(data, indent=2)


def run_blocker(argv=None):
    parser = argparse.ArgumentParser(
        prog="cronwarden blocker",
        description="Detect cron jobs with overlapping schedules.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    parser.add_argument(
        "--fail-on-conflict", action="store_true", help="Exit 1 if conflicts found"
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(1)

    result = find_conflicts(config)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    if args.fail_on_conflict and result.has_conflicts:
        sys.exit(1)

    sys.exit(0)
