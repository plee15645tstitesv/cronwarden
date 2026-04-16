"""CLI entry point for the pin/drift-detection command."""

import argparse
import json
import sys

from cronwarden.config import load_config, ConfigError
from cronwarden.pinner import check_pins


def _parse_pin_args(raw: list[str]) -> dict[str, dict[str, str]]:
    """Parse repeated --pin SERVER/JOB=SCHEDULE arguments.

    Example: --pin 'web/backup=0 2 * * *'
    """
    pins: dict[str, dict[str, str]] = {}
    for item in raw:
        if "/" not in item or "=" not in item:
            raise ValueError(f"Invalid pin format (expected SERVER/JOB=SCHEDULE): {item}")
        location, schedule = item.split("=", 1)
        server, job = location.split("/", 1)
        pins.setdefault(server.strip(), {})[job.strip()] = schedule.strip()
    return pins


def run_pin(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden pin",
        description="Detect schedule drift against pinned expected values.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--pin",
        dest="pins",
        metavar="SERVER/JOB=SCHEDULE",
        action="append",
        default=[],
        help="Pin a job to an expected schedule (repeatable)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit with code 1 if any drift is detected",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 1

    try:
        pins = _parse_pin_args(args.pins)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    result = check_pins(config, pins)

    if args.format == "json":
        output = {
            "total": result.total,
            "drift_count": result.drift_count,
            "has_drift": result.has_drift,
            "pins": [
                {
                    "server": p.server,
                    "job": p.job_name,
                    "expected": p.expected_schedule,
                    "actual": p.actual_schedule,
                    "drifted": p.has_drifted,
                }
                for p in result.pins
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        if not result.pins:
            print("No pins defined.")
        else:
            for pin in result.pins:
                print(pin.summary())
            print(f"\n{result.drift_count}/{result.total} jobs have drifted.")

    if args.fail_on_drift and result.has_drift:
        return 1
    return 0
