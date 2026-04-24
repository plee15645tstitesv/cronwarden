import argparse
import json
import sys

from cronwarden.config import load_config, ConfigError
from cronwarden.auditor_summary import build_audit_summary


def _format_text(report) -> str:
    return str(report)


def _format_json(report) -> str:
    data = {
        "total_servers": report.total_servers,
        "total_jobs": report.total_jobs,
        "valid_jobs": report.valid_jobs,
        "invalid_jobs": report.invalid_jobs,
        "lint_warnings": report.lint_warnings,
        "average_score": round(report.average_score, 2),
        "health_percent": round(report.health_percent, 2),
        "is_healthy": report.is_healthy,
        "top_issues": report.top_issues,
    }
    return json.dumps(data, indent=2)


def run_audit_summary(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden audit-summary",
        description="Display a consolidated audit summary for all cron jobs.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with code 1 if any issues are found",
    )

    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    report = build_audit_summary(config)

    if args.format == "json":
        print(_format_json(report))
    else:
        print(_format_text(report))

    if args.fail_on_issues and not report.is_healthy:
        return 1

    return 0
