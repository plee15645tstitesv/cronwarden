"""Tests for cronwarden.cli_trendier."""
from __future__ import annotations
import json
import os
from pathlib import Path
import pytest
from cronwarden.cli_trendier import run_trend
from cronwarden.snapshotter import save_snapshot
from cronwarden.config import CronJob, Server, Config


@pytest.fixture()
def snapshot_dir(tmp_path: Path) -> Path:
    return tmp_path / "snaps"


def _make_config(n_jobs: int = 2) -> Config:
    jobs = [CronJob(name=f"job{i}", schedule="0 * * * *", command="echo hi") for i in range(n_jobs)]
    server = Server(name="web", host="localhost", jobs=jobs)
    return Config(servers=[server])


def test_run_trend_exits_zero_empty_dir(snapshot_dir: Path):
    snapshot_dir.mkdir()
    rc = run_trend([str(snapshot_dir)])
    assert rc == 0


def test_run_trend_exits_one_for_missing_dir(tmp_path: Path):
    rc = run_trend([str(tmp_path / "nonexistent")])
    assert rc == 1


def test_run_trend_text_output_contains_header(snapshot_dir: Path, capsys):
    snapshot_dir.mkdir()
    save_snapshot(_make_config(), snapshot_dir, label="v1")
    save_snapshot(_make_config(4), snapshot_dir, label="v2")
    run_trend([str(snapshot_dir)])
    captured = capsys.readouterr()
    assert "Trend" in captured.out


def test_run_trend_json_output_is_valid(snapshot_dir: Path, capsys):
    snapshot_dir.mkdir()
    save_snapshot(_make_config(), snapshot_dir, label="v1")
    run_trend([str(snapshot_dir), "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "points" in data
    assert "total_snapshots" in data


def test_run_trend_json_growing_field(snapshot_dir: Path, capsys):
    snapshot_dir.mkdir()
    save_snapshot(_make_config(1), snapshot_dir, label="v1")
    save_snapshot(_make_config(5), snapshot_dir, label="v2")
    run_trend([str(snapshot_dir), "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["growing"] is True


def test_run_trend_json_peak_populated(snapshot_dir: Path, capsys):
    snapshot_dir.mkdir()
    save_snapshot(_make_config(3), snapshot_dir, label="peak")
    run_trend([str(snapshot_dir), "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["peak"] is not None
    assert data["peak"]["label"] == "peak"
