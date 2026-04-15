"""Tests for cronwarden.snapshotter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwarden.config import Config, CronJob, Server
from cronwarden.snapshotter import (
    SnapshotError,
    list_snapshots,
    load_snapshot,
    save_snapshot,
)


def _make_config() -> Config:
    jobs = [
        CronJob(name="backup", schedule="0 2 * * *", command="/usr/bin/backup.sh"),
        CronJob(
            name="cleanup",
            schedule="@daily",
            command="/usr/bin/cleanup.sh",
            description="Daily cleanup",
        ),
    ]
    server = Server(name="prod", host="prod.example.com", jobs=jobs)
    return Config(servers=[server])


def test_save_snapshot_creates_file(tmp_path):
    config = _make_config()
    path = save_snapshot(config, snapshot_dir=tmp_path)
    assert path.exists()
    assert path.suffix == ".json"


def test_save_snapshot_with_label(tmp_path):
    config = _make_config()
    path = save_snapshot(config, label="before-deploy", snapshot_dir=tmp_path)
    assert "before-deploy" in path.name


def test_save_snapshot_content_is_valid_json(tmp_path):
    config = _make_config()
    path = save_snapshot(config, snapshot_dir=tmp_path)
    data = json.loads(path.read_text())
    assert "saved_at" in data
    assert "config" in data
    assert "servers" in data["config"]


def test_load_snapshot_restores_config(tmp_path):
    original = _make_config()
    path = save_snapshot(original, snapshot_dir=tmp_path)
    restored = load_snapshot(path)
    assert isinstance(restored, Config)
    assert len(restored.servers) == 1
    assert restored.servers[0].name == "prod"
    assert len(restored.servers[0].jobs) == 2


def test_load_snapshot_preserves_job_fields(tmp_path):
    original = _make_config()
    path = save_snapshot(original, snapshot_dir=tmp_path)
    restored = load_snapshot(path)
    job = restored.servers[0].jobs[1]
    assert job.name == "cleanup"
    assert job.schedule == "@daily"
    assert job.description == "Daily cleanup"


def test_load_snapshot_missing_file_raises(tmp_path):
    with pytest.raises(SnapshotError, match="not found"):
        load_snapshot(tmp_path / "nonexistent.json")


def test_load_snapshot_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")
    with pytest.raises(SnapshotError, match="Invalid snapshot"):
        load_snapshot(bad)


def test_list_snapshots_returns_sorted_paths(tmp_path):
    config = _make_config()
    p1 = save_snapshot(config, label="a", snapshot_dir=tmp_path)
    p2 = save_snapshot(config, label="b", snapshot_dir=tmp_path)
    result = list_snapshots(snapshot_dir=tmp_path)
    assert len(result) == 2
    assert result == sorted(result)


def test_list_snapshots_empty_when_dir_missing(tmp_path):
    result = list_snapshots(snapshot_dir=tmp_path / "no_such_dir")
    assert result == []
