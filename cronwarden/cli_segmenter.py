"""CLI entry point for the segmenter command."""

import argparse
import json
import sys

from cronwarden.config import load_config, ConfigError
from cronwarden.segmenter import segment_config, SEGMENT_LABELS


def _format_text(result) -> str:
    lines = ["Cron Job Segments", "=" * 40]
    counts = result.segment_counts()
    for seg in SEGMENT_LABELS:
        jobs = result.jobs_in_segment(seg)
        lines.append(f"\n[{seg.upper()}] ({counts.get(seg, 0)} jobs)")
        if jobs:
            for entry in jobs:
                lines.append(f"  {entry.summary()}")
        else:
            lines.append("  (none)")
    lines.append(f"\nTotal: {result.total} jobs")
    return "\n".join(lines)


def _format_json(result) -> str:
    data = {
        "total": result.total,
        "segments": {
            seg: [
                {
                    "server": e.server,
                    "job_name": e.job_name,
                    "schedule": e.schedule,
                    "segment": e.segment,
                }
                for e in result.jobs_in_segment(seg)
            ]
            for seg in SEGMENT_LABELS
        },
    }
    return json.dumps(data, indent=2)


def run_segment(args=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden segment",
        description="Segment cron jobs into time-based buckets.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--segment",
        choices=SEGMENT_LABELS,
        default=None,
        help="Filter output to a specific segment",
    )
    parsed = parser.parse_args(args)

    try:
        config = load_config(parsed.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = segment_config(config)

    if parsed.format == "json":
        print(_format_json(result))
    else:
        if parsed.segment:
            jobs = result.jobs_in_segment(parsed.segment)
            print(f"[{parsed.segment.upper()}] {len(jobs)} job(s)")
            for entry in jobs:
                print(f"  {entry.summary()}")
        else:
            print(_format_text(result))

    return 0
