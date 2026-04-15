"""CLI subcommand for managing cron config snapshots."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwarden.config import load_config, ConfigError
from cronwarden.differ import diff_configs
from cronwarden.formatter import render
from cronwarden.snapshotter import (
    DEFAULT_SNAPSHOT_DIR,
    SnapshotError,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


def run_snapshot(argv: list[str] | None = None) -> int:
    """Entry point for the snapshot subcommand. Returns exit code."""
    parser = argparse.ArgumentParser(
        prog="cronwarden snapshot",
        description="Save and compare cron config snapshots.",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    save_p = sub.add_parser("save", help="Save a snapshot of the current config.")
    save_p.add_argument("config", help="Path to cronwarden config file.")
    save_p.add_argument("--label", default=None, help="Optional label for the snapshot.")
    save_p.add_argument(
        "--snapshot-dir", default=str(DEFAULT_SNAPSHOT_DIR), help="Snapshot directory."
    )

    list_p = sub.add_parser("list", help="List available snapshots.")
    list_p.add_argument(
        "--snapshot-dir", default=str(DEFAULT_SNAPSHOT_DIR), help="Snapshot directory."
    )

    diff_p = sub.add_parser("diff", help="Diff current config against a snapshot.")
    diff_p.add_argument("config", help="Path to cronwarden config file.")
    diff_p.add_argument("snapshot", help="Path to snapshot file to compare against.")
    diff_p.add_argument(
        "--format", choices=["text", "json"], default="text", dest="fmt"
    )

    args = parser.parse_args(argv)
    snapshot_dir = Path(getattr(args, "snapshot_dir", str(DEFAULT_SNAPSHOT_DIR)))

    if args.action == "save":
        try:
            config = load_config(args.config)
        except ConfigError as exc:
            print(f"Error loading config: {exc}", file=sys.stderr)
            return 1
        path = save_snapshot(config, label=args.label, snapshot_dir=snapshot_dir)
        print(f"Snapshot saved: {path}")
        return 0

    if args.action == "list":
        snapshots = list_snapshots(snapshot_dir=snapshot_dir)
        if not snapshots:
            print("No snapshots found.")
        for p in snapshots:
            print(p)
        return 0

    if args.action == "diff":
        try:
            current = load_config(args.config)
            baseline = load_snapshot(Path(args.snapshot))
        except (ConfigError, SnapshotError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        result = diff_configs(baseline, current)
        if not result.has_changes():
            print("No changes detected.")
            return 0
        print(result.summary())
        return 0

    return 1
