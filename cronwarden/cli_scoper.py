"""CLI entry point for the scope analysis command."""
import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.scoper import analyze_scope, ScopeResult


def _format_text(result: ScopeResult, show_all: bool = False) -> str:
    lines = []
    if result.is_empty:
        lines.append("No jobs found.")
        return "\n".join(lines)

    lines.append(f"Scope Analysis  ({result.total} jobs, "
                 f"{len(result.overlapping_entries())} overlapping)")
    lines.append("-" * 60)

    entries = result.entries if show_all else result.overlapping_entries()
    if not entries:
        lines.append("No scope overlaps detected.")
    else:
        for entry in entries:
            lines.append(f"  {entry.summary()}")

    return "\n".join(lines)


def _format_json(result: ScopeResult) -> str:
    data = [
        {
            "server": e.server,
            "job": e.job_name,
            "command": e.command,
            "scope": e.scope,
            "overlap_with": e.overlap_with,
        }
        for e in result.entries
    ]
    return json.dumps({"total": result.total, "has_overlaps": result.has_overlaps,
                       "entries": data}, indent=2)


def run_scope(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden scope",
        description="Analyse cron jobs for overlapping resource scopes.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--all", dest="show_all", action="store_true",
                        help="Show all jobs, not just overlapping ones")
    parser.add_argument("--fail-on-overlap", action="store_true",
                        help="Exit with code 1 if any overlaps are found")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = analyze_scope(config)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result, show_all=args.show_all))

    if args.fail_on_overlap and result.has_overlaps:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run_scope())
