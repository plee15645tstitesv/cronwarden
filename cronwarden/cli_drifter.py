"""CLI entry point for the drift detection command."""
import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.drifter import detect_drift, DriftResult


def _format_text(result: DriftResult) -> str:
    lines = []
    if not result.has_drift and not result.missing_in_baseline and not result.missing_in_current:
        lines.append("No schedule drift detected.")
        return "\n".join(lines)

    if result.drifted:
        lines.append(f"Drifted jobs ({result.total}):")
        for d in result.drifted:
            lines.append(f"  ~ {d.summary()}")

    if result.missing_in_baseline:
        lines.append("New jobs (not in baseline):")
        for name in result.missing_in_baseline:
            lines.append(f"  + {name}")

    if result.missing_in_current:
        lines.append("Removed jobs (in baseline, not in current):")
        for name in result.missing_in_current:
            lines.append(f"  - {name}")

    return "\n".join(lines)


def _format_json(result: DriftResult) -> str:
    return json.dumps({
        "drifted": [
            {
                "server": d.server,
                "job": d.job_name,
                "baseline_schedule": d.baseline_schedule,
                "current_schedule": d.current_schedule,
            }
            for d in result.drifted
        ],
        "missing_in_baseline": result.missing_in_baseline,
        "missing_in_current": result.missing_in_current,
        "has_drift": result.has_drift,
        "total": result.total,
    }, indent=2)


def run_drift(argv=None):
    parser = argparse.ArgumentParser(description="Detect schedule drift against a snapshot.")
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument("snapshot", help="Path to baseline snapshot JSON file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--fail-on-drift", action="store_true",
                        help="Exit with code 1 if drift is detected")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        result = detect_drift(config, args.snapshot)
    except Exception as exc:
        print(f"Error reading snapshot: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    if args.fail_on_drift and result.has_drift:
        sys.exit(1)
