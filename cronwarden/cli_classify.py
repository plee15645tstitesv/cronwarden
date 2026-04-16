"""CLI entry point for the classify command."""

import argparse
import json
import sys

from cronwarden.config import load_config, ConfigError
from cronwarden.classifier import classify_config


def _format_text(result) -> str:
    lines = []
    by_cat = result.by_category()
    for category, jobs in sorted(by_cat.items()):
        lines.append(f"[{category.upper()}]")
        for cj in jobs:
            lines.append(f"  {cj.server}/{cj.job.name}: {cj.job.command}")
    if result.unclassified:
        lines.append("[UNCLASSIFIED]")
        for server_name, job in result.unclassified:
            lines.append(f"  {server_name}/{job.name}: {job.command}")
    lines.append("")
    lines.append(f"Total: {result.total()} jobs, {len(result.classified)} classified, {len(result.unclassified)} unclassified.")
    return "\n".join(lines)


def _format_json(result) -> str:
    by_cat = result.by_category()
    data = {
        "classified": {
            cat: [{"server": cj.server, "job": cj.job.name, "command": cj.job.command} for cj in jobs]
            for cat, jobs in by_cat.items()
        },
        "unclassified": [
            {"server": s, "job": j.name, "command": j.command}
            for s, j in result.unclassified
        ],
        "total": result.total(),
    }
    return json.dumps(data, indent=2)


def run_classify(argv=None):
    parser = argparse.ArgumentParser(description="Classify cron jobs by category")
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = classify_config(config)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    sys.exit(0)
