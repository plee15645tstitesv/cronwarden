import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.profiler import profile_config


def _format_text(result) -> str:
    if result.is_empty():
        return "No jobs found."
    lines = []
    for p in result.profiles:
        desc = "(no description)" if not p.has_description else ""
        lines.append(
            f"  [{p.risk_level.upper():6}] {p.server}/{p.job_name} "
            f"| {p.schedule} | {p.command} {desc}".strip()
        )
    high = len(result.by_risk("high"))
    med = len(result.by_risk("medium"))
    low = len(result.by_risk("low"))
    lines.append(f"\nTotal: {result.total()} | High: {high} | Medium: {med} | Low: {low}")
    return "\n".join(lines)


def _format_json(result) -> str:
    data = [
        {
            "server": p.server,
            "job": p.job_name,
            "schedule": p.schedule,
            "command": p.command,
            "tags": p.tags,
            "has_description": p.has_description,
            "estimated_duration": p.estimated_duration,
            "risk_level": p.risk_level,
        }
        for p in result.profiles
    ]
    return json.dumps(data, indent=2)


def run_profile(argv=None):
    parser = argparse.ArgumentParser(description="Profile cron jobs by risk and characteristics")
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--risk", choices=["high", "medium", "low"], help="Filter by risk level")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = profile_config(config)

    if args.risk:
        from cronwarden.profiler import ProfileResult
        filtered = ProfileResult(profiles=result.by_risk(args.risk))
        result = filtered

    output = _format_json(result) if args.format == "json" else _format_text(result)
    print(output)
    sys.exit(0)
