from __future__ import annotations
import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.alerter import check_alerts, AlertResult


def _format_text(result: AlertResult) -> str:
    if not result.has_alerts:
        return "No alerts found.\n"
    lines = []
    for alert in result.alerts:
        lines.append(alert.summary())
    lines.append(f"\nTotal: {result.total} alert(s)")
    return "\n".join(lines) + "\n"


def _format_json(result: AlertResult) -> str:
    data = [
        {
            "server": a.server,
            "job": a.job_name,
            "level": a.level,
            "message": a.message,
        }
        for a in result.alerts
    ]
    return json.dumps(data, indent=2)


def run_alert(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden alert",
        description="Check cron jobs for alert conditions",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--level",
        choices=["critical", "warning", "info"],
        default=None,
        help="Filter alerts by level",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
    )
    parser.add_argument(
        "--fail-on-critical",
        action="store_true",
        help="Exit with code 2 if any critical alerts are found",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = check_alerts(config, level_filter=args.level)

    if args.fmt == "json":
        print(_format_json(result))
    else:
        print(_format_text(result), end="")

    if args.fail_on_critical and result.critical:
        return 2
    return 0
