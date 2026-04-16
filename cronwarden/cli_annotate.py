"""CLI entry point for the annotate command."""
import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.annotator import annotate_config, list_annotations


def _parse_notes(raw: list) -> dict:
    """Parse 'server:job:note' strings into nested dict."""
    notes: dict = {}
    for item in raw:
        parts = item.split(":", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid annotation format (expected server:job:note): {item}")
        server, job, note = parts
        notes.setdefault(server, {})[job] = note
    return notes


def run_annotate(argv=None):
    parser = argparse.ArgumentParser(
        prog="cronwarden annotate",
        description="Attach notes to cron jobs and display them.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--note",
        dest="notes",
        action="append",
        default=[],
        metavar="SERVER:JOB:NOTE",
        help="Annotation in server:job:note format (repeatable)",
    )
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        notes = _parse_notes(args.notes)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    result = annotate_config(config, notes)

    if args.format == "json":
        data = [
            {"server": a.server, "job": a.job_name, "note": a.note}
            for a in result.annotations
        ]
        print(json.dumps(data, indent=2))
    else:
        if not result.has_annotations:
            print("No annotations.")
        else:
            for line in list_annotations(result):
                print(line)

    sys.exit(0)
