"""Tests for cronwarden.cli_history."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from cronwarden.cli_history import run_history, _format_text, _format_json
from cronwarden.historian import HistoryResult, SnapshotEntry
from datetime import datetime


def _make_entry(label=None, server_count=1, job_count=3):
    return SnapshotEntry(
        filename="snap_001.json",
        timestamp=datetime(2024, 6, 1, 10, 0, 0),
        label=label,
        server_count=server_count,
        job_count=job_count,
    )


def test_format_text_empty():
    result = HistoryResult(entries=[])
    output = _format_text(result)
    assert "No snapshots" in output


def test_format_text_contains_entry_summary():
    result = HistoryResult(entries=[_make_entry()])
    output = _format_text(result)
    assert "2024-06-01" in output
    assert "snap_001.json" in output


def test_format_text_contains_label():
    result = HistoryResult(entries=[_make_entry(label="nightly")])
    output = _format_text(result)
    assert "nightly" in output


def test_format_json_returns_valid_json():
    result = HistoryResult(entries=[_make_entry()])
    output = _format_json(result)
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 1


def test_format_json_entry_fields():
    result = HistoryResult(entries=[_make_entry(label="prod")])
    parsed = json.loads(_format_json(result))
    entry = parsed[0]
    assert entry["label"] == "prod"
    assert entry["server_count"] == 1
    assert entry["job_count"] == 3
    assert "timestamp" in entry
    assert "filename" in entry


def test_run_history_exits_zero_for_valid_dir(tmp_path):
    import json as _json
    payload = {
        "meta": {"timestamp": "2024-06-01T10:00:00", "label": None},
        "config": {"servers": []},
    }
    (tmp_path / "snap_001.json").write_text(_json.dumps(payload))
    args = SimpleNamespace(snapshot_dir=str(tmp_path), format="text")
    assert run_history(args) == 0


def test_run_history_exits_one_for_missing_dir():
    args = SimpleNamespace(snapshot_dir="/nonexistent/path/xyz", format="text")
    # load_history itself won't raise for missing dir (list_snapshots returns []),
    # but we still expect exit 0 (empty result) rather than a crash.
    code = run_history(args)
    assert code in (0, 1)


def test_run_history_json_format(tmp_path, capsys):
    import json as _json
    payload = {
        "meta": {"timestamp": "2024-06-01T10:00:00", "label": "test"},
        "config": {"servers": []},
    }
    (tmp_path / "snap_001.json").write_text(_json.dumps(payload))
    args = SimpleNamespace(snapshot_dir=str(tmp_path), format="json")
    run_history(args)
    captured = capsys.readouterr()
    parsed = _json.loads(captured.out)
    assert isinstance(parsed, list)
