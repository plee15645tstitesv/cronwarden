"""CLI entry point for the scope overlap analysis command."""

import argparse
import json
import sys

from cronwarden.config import ConfigError, load_config
from cronwarden.scoper import ScopedJob, ScopeResult, scope_config


def _format_text(result: ScopeResult) -> str:
    """Render scope analysis result as human-readable text."""
    lines = []
    lines.append(f"Scope Analysis — {result.total} job(s) examined")
    if result.has_overlaps:
        lines.append(f"Overlapping scopes detected: {len([e for e in result.entries if e.overlaps])}")
    else:
        lines.append("No scope overlaps detected.")
    lines.append("")

    for entry in result.entries:
        overlap_marker = " [OVERLAP]" if entry.overlaps else ""
        lines.append(f"  [{entry.server}] {entry.job.name}{overlap_marker}")
        lines.append(f"    Schedule : {entry.job.schedule}")
        lines.append(f"    Scope    : {entry.summary()}")
        if entry.overlaps and entry.overlap_with:
            lines.append(f"    Conflicts: {', '.join(entry.overlap_with)}")
        lines.append("")

    return "\n".join(lines).rstrip()


def _format_json(result: ScopeResult) -> str:
    """Render scope analysis result as JSON."""
    data = {
        "total": result.total,
        "has_overlaps": result.has_overlaps,
        "entries": [
            {
                "server": e.server,
                "job": e.job.name,
                "schedule": e.job.schedule,
                "scope_summary": e.summary(),
                "overlaps": e.overlaps,
                "overlap_with": e.overlap_with,
            }
            for e in result.entries
        ],
    }
    return json.dumps(data, indent=2)


def run_scope(argv: list[str] | None = None) -> int:
    """Run the scope overlap analysis command.

    Returns an exit code: 0 on success, 1 on error or when --fail-on-overlap
    is set and overlaps are found.
    """
    parser = argparse.ArgumentParser(
        prog="cronwarden scope",
        description="Analyse schedule scope and detect overlapping cron jobs.",
    )
    parser.add_argument("config", help="Path to the cronwarden config file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-overlap",
        action="store_true",
        default=False,
        help="Exit with code 1 when scope overlaps are detected",
    )
    parser.add_argument(
        "--server",
        default=None,
        metavar="SERVER",
        help="Limit analysis to a specific server name",
    )

    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 1

    result = scope_config(config, server_filter=args.server)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    if args.fail_on_overlap and result.has_overlaps:
        return 1

    return 0
