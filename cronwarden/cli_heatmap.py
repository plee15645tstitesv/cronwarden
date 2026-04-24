"""CLI entry point for the heatmap command."""

import argparse
import json
import sys

from cronwarden.config import ConfigError, load_config
from cronwarden.heatmap import HeatmapResult, build_heatmap


def _format_text(result: HeatmapResult) -> str:
    lines = [f"Heatmap — {result.total_jobs} job(s) analysed"]
    if result.is_empty():
        lines.append("  (no data)")
        return "\n".join(lines)

    peak = result.peak_cell()
    if peak:
        lines.append(f"  Peak: {peak.summary()}")

    lines.append("")
    for cell in result.cells:
        bar = "#" * cell.count
        lines.append(f"  {cell.summary():<30} {bar}")
    return "\n".join(lines)


def _format_json(result: HeatmapResult) -> str:
    return json.dumps(result.to_dict(), indent=2)


def run_heatmap(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden heatmap",
        description="Show a frequency heatmap of cron job execution times.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = build_heatmap(config)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    return 0
