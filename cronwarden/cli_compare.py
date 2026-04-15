"""CLI entry point for comparing two cronwarden config files."""

import json
import sys
from argparse import ArgumentParser, Namespace

from cronwarden.config import load_config, ConfigError
from cronwarden.comparator import compare_configs, ComparisonResult


def _format_text(result: ComparisonResult) -> str:
    return str(result)


def _format_json(result: ComparisonResult) -> str:
    data = {
        "left": result.left_label,
        "right": result.right_label,
        "total_differences": result.total(),
        "differences": [
            {
                "server": d.server,
                "job": d.job_name,
                "field": d.field,
                "left": d.left_value,
                "right": d.right_value,
            }
            for d in result.differences
        ],
    }
    return json.dumps(data, indent=2)


def run_compare(argv: list = None) -> int:
    parser = ArgumentParser(
        prog="cronwarden compare",
        description="Compare two cronwarden config files.",
    )
    parser.add_argument("left", help="Path to the first (base) config file")
    parser.add_argument("right", help="Path to the second (target) config file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    args: Namespace = parser.parse_args(argv)

    try:
        left_config = load_config(args.left)
        right_config = load_config(args.right)
    except ConfigError as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 1

    result = compare_configs(
        left_config,
        right_config,
        left_label=args.left,
        right_label=args.right,
    )

    if args.fmt == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    return 1 if result.has_differences() else 0
