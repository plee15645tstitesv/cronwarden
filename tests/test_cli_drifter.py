"""Tests for cronwarden.cli_drifter."""
import json
import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.snapshotter import save_snapshot
from cronwarden.cli_drifter import run_drift


def _make_job(name, schedule="0 * * * *"):
    return CronJob(name=name, schedule=schedule, command="echo ok")


def _make_config(server_name="prod", jobs=None):
    if jobs is None:
        jobs = [_make_job("daily", "@daily")]
    return Config(servers=[Server(name=server_name, host="localhost", jobs=jobs)])


@pytest.fixture()
def snapshot_and_config(tmp_path):
    cfg = _make_config()
    snap = str(tmp_path / "baseline.json")
    save_snapshot(cfg, snap)
    config_path = tmp_path / "cronwarden.yaml"
    config_path.write_text(
        "servers:\n"
        "  - name: prod\n"
        "    host: localhost\n"
        "    jobs:\n"
        "      - name: daily\n"
        "        schedule: '@daily'\n"
        "        command: echo ok\n"
    )
    return str(config_path), snap


def _run(argv, capsys):
    try:
        run_drift(argv)
        code = 0
    except SystemExit as e:
        code = e.code
    return code, capsys.readouterr()


def test_run_drift_exits_zero_no_drift(snapshot_and_config, capsys):
    config_path, snap = snapshot_and_config
    code, _ = _run([config_path, snap], capsys)
    assert code == 0


def test_run_drift_text_output_no_drift(snapshot_and_config, capsys):
    config_path, snap = snapshot_and_config
    _run([config_path, snap], capsys)
    out = capsys.readouterr().out
    assert "No schedule drift" in out


def test_run_drift_json_output_is_valid(snapshot_and_config, capsys):
    config_path, snap = snapshot_and_config
    _run([config_path, snap, "--format", "json"], capsys)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "drifted" in data
    assert "has_drift" in data


def test_run_drift_bad_config_exits_one(tmp_path, capsys):
    snap = str(tmp_path / "snap.json")
    code, _ = _run([str(tmp_path / "missing.yaml"), snap], capsys)
    assert code == 1


def test_run_drift_bad_snapshot_exits_one(tmp_path, capsys):
    config_path = tmp_path / "cronwarden.yaml"
    config_path.write_text(
        "servers:\n"
        "  - name: prod\n"
        "    host: localhost\n"
        "    jobs:\n"
        "      - name: daily\n"
        "        schedule: '@daily'\n"
        "        command: echo ok\n"
    )
    code, _ = _run([str(config_path), str(tmp_path / "nosnapshot.json")], capsys)
    assert code == 1


def test_run_drift_fail_on_drift_exits_one(tmp_path, capsys):
    cfg_baseline = _make_config(jobs=[_make_job("daily", "@daily")])
    snap = str(tmp_path / "snap.json")
    save_snapshot(cfg_baseline, snap)
    config_path = tmp_path / "cronwarden.yaml"
    config_path.write_text(
        "servers:\n"
        "  - name: prod\n"
        "    host: localhost\n"
        "    jobs:\n"
        "      - name: daily\n"
        "        schedule: '@hourly'\n"
        "        command: echo ok\n"
    )
    code, _ = _run([str(config_path), snap, "--fail-on-drift"], capsys)
    assert code == 1
