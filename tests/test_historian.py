"""Tests for cronwarden.historian."""

from __future__ import annotations

import json
import os
from datetime import datetime

import pytest

from cronwarden.historian import load_history, SnapshotEntry, HistoryResult
from cronwarden.config import Config, Server, CronJob


def _make_snapshot(tmp_path, filename, label=None, servers=None):
    """Write a minimal snapshot JSON file."""
    servers = servers or [
        {"name": "web", "host": "web.example.com", "jobs": [
            {"name": "backup", "schedule": "0 2 * * *", "command": "backup.sh"}
        ]}
    ]
    payload = {
        "meta": {
            "timestamp": "2024-06-01T10:00:00",
            "label": label,
        },
        "config": {"servers": servers},
    }
    if label:
        payload["meta"]["label"] = label
    path = tmp_path / filename
    path.write_text(json.dumps(payload))
    return str(path)


def test_load_history_returns_history_result(tmp_path):
    _make_snapshot(tmp_path, "snap_001.json")
    result = load_history(str(tmp_path))
    assert isinstance(result, HistoryResult)


def test_load_history_empty_dir(tmp_path):
    result = load_history(str(tmp_path))
    assert result.is_empty()
    assert result.latest() is None
    assert result.oldest() is None


def test_load_history_counts_entries(tmp_path):
    _make_snapshot(tmp_path, "snap_001.json")
    _make_snapshot(tmp_path, "snap_002.json")
    result = load_history(str(tmp_path))
    assert len(result.entries) == 2


def test_load_history_entry_fields(tmp_path):
    _make_snapshot(tmp_path, "snap_001.json", label="weekly")
    result = load_history(str(tmp_path))
    entry = result.entries[0]
    assert entry.label == "weekly"
    assert entry.server_count == 1
    assert entry.job_count == 1
    assert isinstance(entry.timestamp, datetime)


def test_load_history_sorted_newest_first(tmp_path):
    snap1 = json.loads((tmp_path / "snap_a.json").read_text()) if False else None
    # write two snapshots with different timestamps
    for fname, ts in [("snap_a.json", "2024-01-01T00:00:00"), ("snap_b.json", "2024-06-01T00:00:00")]:
        payload = {
            "meta": {"timestamp": ts, "label": None},
            "config": {"servers": []},
        }
        (tmp_path / fname).write_text(json.dumps(payload))

    result = load_history(str(tmp_path))
    assert result.entries[0].timestamp > result.entries[1].timestamp


def test_snapshot_entry_summary_includes_timestamp(tmp_path):
    _make_snapshot(tmp_path, "snap_001.json")
    result = load_history(str(tmp_path))
    summary = result.entries[0].summary()
    assert "2024-06-01" in summary
    assert "server" in summary


def test_snapshot_entry_summary_includes_label(tmp_path):
    _make_snapshot(tmp_path, "snap_001.json", label="prod-weekly")
    result = load_history(str(tmp_path))
    assert "prod-weekly" in result.entries[0].summary()


def test_load_history_skips_invalid_files(tmp_path):
    (tmp_path / "broken.json").write_text("not json at all")
    _make_snapshot(tmp_path, "snap_001.json")
    result = load_history(str(tmp_path))
    assert len(result.entries) == 1
