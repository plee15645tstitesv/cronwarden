"""CLI entry point for the outlier detection command."""

import argparse
import json
import sys

from cronwarden.config import load_config, ConfigError
from cronwarden.outlier import find_outliers, OutlierResult


def _format_text(result: OutlierResult, severity: str | None) -> str:
    lines = []
    items = result.outliers
    if severity:
        items = result.by_severity(severity)
    if not items:
        lines.append("No outliers detected.")
        return "\n".join(lines)
    lines.append(f"Outliers detected: {len(items)}")
    lines.append("")
    for o in items:
        lines.append(f"  {o.summary()}")
    return "\n".join(lines)


def _format_json(result: OutlierResult, severity: str | None) -> str:
    items = result.outliers
    if severity:
        items = result.by_severity(severity)
    data = [
        {
            "server": o.server,
            "job": o.job_name,
            "schedule": o.schedule,
            "reason": o.reason,
            "severity": o.severity,
        }
        for o in items
    ]
    return json.dumps({"total": len(data), "outliers": data}, indent=2)


def run_outlier(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden outlier",
        description="Detect outlier cron jobs with unusual scheduling patterns.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--severity", choices=["low", "medium", "high"], default=None,
                        help="Filter outliers by severity level")
    parser.add_argument("--fail-on-outliers", action="store_true",
                        help="Exit with code 1 if any outliers are found")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = find_outliers(config)

    if args.format == "json":
        print(_format_json(result, args.severity))
    else:
        print(_format_text(result, args.severity))

    if args.fail_on_outliers and result.has_outliers:
        return 1
    return 0
