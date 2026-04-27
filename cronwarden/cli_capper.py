"""cli_capper.py — CLI entry-point for the capper module."""
from __future__ import annotations

import argparse
import json
import sys

from cronwarden.capper import check_cap
from cronwarden.config import ConfigError, load_config


def _format_text(result) -> str:
    return result.summary()


def _format_json(result) -> str:
    data = [
        {
            "server": c.server,
            "job": c.job_name,
            "schedule": c.schedule,
            "runs_per_day": round(c.runs_per_day, 2),
            "cap": c.cap,
        }
        for c in result.capped
    ]
    return json.dumps({"over_capped": data, "total": result.total}, indent=2)


def run_cap(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden cap",
        description="Detect jobs that exceed a maximum run-frequency cap.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--cap",
        type=float,
        default=96.0,
        metavar="N",
        help="Maximum allowed runs per day (default: 96)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
    )
    parser.add_argument(
        "--fail-on-capped",
        action="store_true",
        help="Exit with code 1 when over-capped jobs are found",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = check_cap(config, cap=args.cap)

    output = _format_json(result) if args.fmt == "json" else _format_text(result)
    print(output)

    if args.fail_on_capped and result.has_capped:
        return 1
    return 0
