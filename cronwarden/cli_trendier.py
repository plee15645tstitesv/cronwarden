"""CLI entry point for the trend analysis command."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from cronwarden.historian import load_history
from cronwarden.trendier import build_trend, TrendResult


def _format_text(result: TrendResult) -> str:
    if result.is_empty:
        return "No snapshot history found for trend analysis."
    lines = ["Trend Analysis", "=" * 40]
    for point in result.points:
        lines.append(point.summary())
    lines.append("")
    if result.growing is True:
        lines.append("Trend: ↑ Growing")
    elif result.growing is False:
        lines.append("Trend: ↓ Shrinking")
    else:
        lines.append("Trend: → Stable")
    if result.peak_point:
        lines.append(f"Peak: {result.peak_point.summary()}")
    return "\n".join(lines)


def _format_json(result: TrendResult) -> str:
    data = {
        "total_snapshots": result.total,
        "growing": result.growing,
        "peak": {
            "label": result.peak_point.label,
            "total_jobs": result.peak_point.total_jobs,
        } if result.peak_point else None,
        "points": [
            {
                "label": p.label,
                "total_jobs": p.total_jobs,
                "invalid_jobs": p.invalid_jobs,
                "server_count": p.server_count,
            }
            for p in result.points
        ],
    }
    return json.dumps(data, indent=2)


def run_trend(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden trend",
        description="Analyse job count trends across snapshot history.",
    )
    parser.add_argument("snapshot_dir", help="Directory containing snapshots")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    snap_dir = Path(args.snapshot_dir)
    if not snap_dir.exists():
        print(f"Error: snapshot directory not found: {snap_dir}", file=sys.stderr)
        return 1

    history = load_history(snap_dir)
    result = build_trend(history.entries)

    output = _format_json(result) if args.format == "json" else _format_text(result)
    print(output)
    return 0
