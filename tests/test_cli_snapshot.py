"""Tests for cronwarden.cli_snapshot."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwarden.cli_snapshot import run_snapshot
from cronwarden.config import Config, CronJob, Server
from cronwarden.snapshotter import save_snapshot


@pytest.fixture()
def config_file(tmp_path):
    content = """
servers:
  - name: web
    host: web.example.com
    jobs:
      - name: cleanup
        schedule: "0 3 * * *"
        command: /usr/bin/cleanup.sh
        description: Nightly cleanup
"""
    p = tmp_path / "cronwarden.yml"
    p.write_text(content)
    return str(p)


@pytest.fixture()
def snapshot_dir(tmp_path):
    return str(tmp_path / "snaps")


def test_save_exits_zero(config_file, snapshot_dir):
    code = run_snapshot(["save", config_file, "--snapshot-dir", snapshot_dir])
    assert code == 0


def test_save_creates_snapshot_file(config_file, snapshot_dir):
    run_snapshot(["save", config_file, "--snapshot-dir", snapshot_dir])
    snaps = list(Path(snapshot_dir).glob("*.json"))
    assert len(snaps) == 1


def test_save_with_label(config_file, snapshot_dir):
    run_snapshot(["save", config_file, "--label", "mysnap", "--snapshot-dir", snapshot_dir])
    snaps = list(Path(snapshot_dir).glob("*.json"))
    assert any("mysnap" in p.name for p in snaps)


def test_list_shows_snapshots(config_file, snapshot_dir, capsys):
    run_snapshot(["save", config_file, "--snapshot-dir", snapshot_dir])
    run_snapshot(["list", "--snapshot-dir", snapshot_dir])
    out = capsys.readouterr().out
    assert ".json" in out


def test_list_empty_snapshot_dir(snapshot_dir, capsys):
    code = run_snapshot(["list", "--snapshot-dir", snapshot_dir])
    out = capsys.readouterr().out
    assert "No snapshots" in out
    assert code == 0


def test_diff_no_changes(config_file, snapshot_dir, capsys):
    run_snapshot(["save", config_file, "--snapshot-dir", snapshot_dir])
    snap = list(Path(snapshot_dir).glob("*.json"))[0]
    code = run_snapshot(["diff", config_file, str(snap)])
    out = capsys.readouterr().out
    assert "No changes" in out
    assert code == 0


def test_diff_missing_snapshot_exits_nonzero(config_file, snapshot_dir):
    code = run_snapshot(["diff", config_file, "/nonexistent/snap.json"])
    assert code != 0


def test_save_invalid_config_exits_nonzero(tmp_path, snapshot_dir):
    bad = tmp_path / "bad.yml"
    bad.write_text("not: valid: cronwarden: config")
    code = run_snapshot(["save", str(bad), "--snapshot-dir", snapshot_dir])
    assert code != 0
