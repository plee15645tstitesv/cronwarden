"""CLI sub-command: cronwarden history — list snapshot history."""

from __future__ import annotations

import json
import sys
from typing import List

from cronwarden.historian import load_history, HistoryResult


def _format_text(result: HistoryResult) -> str:
    if result.is_empty():
        return "No snapshots found."
    lines = ["Snapshot history (newest first):", ""]
    for entry in result.entries:
        lines.append(f"  {entry.summary()}")
        lines.append(f"    file: {entry.filename}")
    return "\n".join(lines)


def _format_json(result: HistoryResult) -> str:
    data = [
        {
            "filename": e.filename,
            "timestamp": e.timestamp.isoformat(),
            "label": e.label,
            "server_count": e.server_count,
            "job_count": e.job_count,
        }
        for e in result.entries
    ]
    return json.dumps(data, indent=2)


def run_history(args) -> int:
    """Entry point for the history sub-command. Returns an exit code."""
    snapshot_dir = getattr(args, "snapshot_dir", "snapshots")
    fmt = getattr(args, "format", "text")

    try:
        result = load_history(snapshot_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"Error reading snapshot directory: {exc}", file=sys.stderr)
        return 1

    output = _format_json(result) if fmt == "json" else _format_text(result)
    print(output)
    return 0
