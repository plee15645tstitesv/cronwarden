"""CLI entry point for the prune command."""

import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.pruner import prune_config, PruneResult


def _format_text(result: PruneResult) -> str:
    return str(result)


def _format_json(result: PruneResult) -> str:
    data = {
        "total_scanned": result.total_scanned,
        "total_pruned": result.total(),
        "pruned": [
            {
                "server": p.server,
                "job": p.job_name,
                "schedule": p.schedule,
                "command": p.command,
                "reason": p.reason,
            }
            for p in result.pruned
        ],
    }
    return json.dumps(data, indent=2)


def run_prune(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden prune",
        description="Flag cron jobs that are candidates for removal.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--never-run",
        nargs="*",
        default=[],
        metavar="JOB_NAME",
        help="Job names known to have never executed",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--fail-on-prune",
        action="store_true",
        help="Exit with code 1 if any pruning candidates are found",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = prune_config(config, never_run_names=args.never_run or None)

    output = _format_json(result) if args.format == "json" else _format_text(result)
    print(output)

    if args.fail_on_prune and result.has_pruned():
        return 1
    return 0
