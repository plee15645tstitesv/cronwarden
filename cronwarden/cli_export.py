"""CLI command for exporting cron job configs."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwarden.config import load_config, ConfigError
from cronwarden.exporter import export_csv, export_table


def run_export(argv: list[str] | None = None) -> int:
    """Entry point for the `cronwarden export` sub-command."""
    parser = argparse.ArgumentParser(
        prog="cronwarden export",
        description="Export cron job definitions to CSV or a plain-text table.",
    )
    parser.add_argument("config", help="Path to cronwarden config file (YAML).")
    parser.add_argument(
        "--format",
        choices=["csv", "table"],
        default="table",
        help="Output format (default: table).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write output to FILE instead of stdout.",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(Path(args.config))
    except ConfigError as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"Config file not found: {args.config}", file=sys.stderr)
        return 1

    if args.format == "csv":
        output = export_csv(config)
    else:
        output = export_table(config)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Exported to {args.output}")
    else:
        print(output)

    return 0
