"""CLI entry point for the rotator feature."""
import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.rotator import rotate_config, RotationResult


def _format_text(result: RotationResult) -> str:
    if not result.has_suggestions:
        return "✔ No rotation suggestions. Schedules look well-spread."
    lines = [f"⚠ {result.total} rotation suggestion(s):\n"]
    for s in result.suggestions:
        lines.append(f"  [{s.server}] {s.job_name}")
        lines.append(f"    current:   {s.current_schedule}")
        lines.append(f"    suggested: {s.suggested_schedule}")
        lines.append(f"    reason:    {s.reason}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _format_json(result: RotationResult) -> str:
    data = {
        "total": result.total,
        "has_suggestions": result.has_suggestions,
        "suggestions": [
            {
                "server": s.server,
                "job": s.job_name,
                "current_schedule": s.current_schedule,
                "suggested_schedule": s.suggested_schedule,
                "reason": s.reason,
            }
            for s in result.suggestions
        ],
    }
    return json.dumps(data, indent=2)


def run_rotate(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden rotate",
        description="Suggest schedule rotations to reduce concurrent job load.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--fail-on-suggestions",
        action="store_true",
        help="Exit with code 1 if any rotation suggestions are found",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 1

    result = rotate_config(config)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    if args.fail_on_suggestions and result.has_suggestions:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run_rotate())
