"""CLI entry point for the balancer command.

Detects schedule imbalances across servers — e.g. too many jobs
clustered at the same minute/hour — and reports them.
"""

from __future__ import annotations

import argparse
import json
import sys

from cronwarden.balancer import BalanceResult, build_balance_report
from cronwarden.config import ConfigError, load_config


def _format_text(result: BalanceResult) -> str:
    """Render balance result as human-readable text."""
    lines: list[str] = []

    if result.is_empty:
        lines.append("No jobs found — nothing to balance.")
        return "\n".join(lines)

    lines.append(f"Schedule Balance Report")
    lines.append(f"  Total jobs analysed : {result.total}")
    lines.append(f"  Imbalances detected : {len(result.imbalances)}")
    lines.append("")

    if not result.has_imbalances:
        lines.append("✓ No schedule imbalances detected.")
        return "\n".join(lines)

    for entry in result.imbalances:
        lines.append(f"  ⚠  {entry.summary()}")

    return "\n".join(lines)


def _format_json(result: BalanceResult) -> str:
    """Render balance result as JSON."""
    payload = {
        "total_jobs": result.total,
        "has_imbalances": result.has_imbalances,
        "imbalances": [
            {
                "slot": entry.slot,
                "dimension": entry.dimension,
                "job_count": entry.job_count,
                "jobs": [
                    {"server": j.server, "name": j.name}
                    for j in entry.jobs
                ],
                "summary": entry.summary(),
            }
            for entry in result.imbalances
        ],
    }
    return json.dumps(payload, indent=2)


def run_balancer(argv: list[str] | None = None) -> int:
    """Parse arguments and run the balancer command.

    Returns an exit code: 0 for success, 1 for errors.
    When *--fail-on-imbalance* is set the exit code is 2 if any
    imbalances are found.
    """
    parser = argparse.ArgumentParser(
        prog="cronwarden balance",
        description="Detect schedule imbalances across servers.",
    )
    parser.add_argument("config", help="Path to the cronwarden config file.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=3,
        metavar="N",
        help="Minimum number of jobs in the same slot to flag as an imbalance (default: 3).",
    )
    parser.add_argument(
        "--dimension",
        choices=["minute", "hour", "both"],
        default="both",
        help="Which schedule dimension to analyse (default: both).",
    )
    parser.add_argument(
        "--fail-on-imbalance",
        action="store_true",
        default=False,
        help="Exit with code 2 if any imbalances are detected.",
    )

    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: config file not found: {args.config}", file=sys.stderr)
        return 1
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = build_balance_report(
        config,
        threshold=args.threshold,
        dimension=args.dimension,
    )

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    if args.fail_on_imbalance and result.has_imbalances:
        return 2

    return 0
