"""Tests for cronwarden.capper."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from cronwarden.capper import CapResult, CappedJob, check_cap
from cronwarden.config import Config, CronJob, Server


def _make_job(name: str, schedule: str) -> CronJob:
    return CronJob(name=name, schedule=schedule, command=f"run_{name}")


def _make_config(*pairs) -> Config:
    """pairs: (server_name, [(job_name, schedule), ...])"""
    servers = []
    for sname, jobs in pairs:
        servers.append(
            Server(name=sname, jobs=[_make_job(jn, s) for jn, s in jobs])
        )
    return Config(servers=servers)


# ── unit: CapResult ────────────────────────────────────────────────────────

def test_cap_result_has_capped_false_when_empty():
    assert CapResult().has_capped is False


def test_cap_result_has_capped_true_when_populated():
    c = CappedJob(server="s", job_name="j", schedule="* * * * *",
                  runs_per_day=1440.0, cap=96.0)
    assert CapResult(capped=[c]).has_capped is True


def test_cap_result_total():
    c = CappedJob(server="s", job_name="j", schedule="* * * * *",
                  runs_per_day=1440.0, cap=96.0)
    assert CapResult(capped=[c, c]).total == 2


def test_cap_result_summary_empty():
    assert "No over-capped" in CapResult().summary()


def test_cap_result_summary_with_entries():
    c = CappedJob(server="web", job_name="ping", schedule="* * * * *",
                  runs_per_day=1440.0, cap=96.0)
    summary = CapResult(capped=[c]).summary()
    assert "web/ping" in summary
    assert "1440" in summary


def test_capped_job_summary_contains_fields():
    c = CappedJob(server="srv", job_name="heartbeat",
                  schedule="*/5 * * * *", runs_per_day=288.0, cap=96.0)
    s = c.summary()
    assert "srv/heartbeat" in s
    assert "288" in s
    assert "96" in s


# ── unit: check_cap ────────────────────────────────────────────────────────

def test_check_cap_returns_cap_result():
    cfg = _make_config(("s1", [("daily", "0 6 * * *")]))
    assert isinstance(check_cap(cfg), CapResult)


def test_every_minute_job_is_over_default_cap():
    cfg = _make_config(("s1", [("noisy", "* * * * *")]))
    result = check_cap(cfg)
    assert result.has_capped
    assert result.capped[0].job_name == "noisy"


def test_daily_job_not_over_default_cap():
    cfg = _make_config(("s1", [("daily", "0 6 * * *")]))
    result = check_cap(cfg)
    assert not result.has_capped


def test_custom_cap_threshold():
    # every 30 minutes = 48 runs/day — fine at cap=96, over at cap=24
    cfg = _make_config(("s1", [("half-hourly", "*/30 * * * *")]))
    assert not check_cap(cfg, cap=96.0).has_capped
    assert check_cap(cfg, cap=24.0).has_capped


def test_multiple_servers_each_checked():
    cfg = _make_config(
        ("s1", [("fast", "* * * * *")]),
        ("s2", [("slow", "0 0 * * *")]),
    )
    result = check_cap(cfg)
    assert result.total == 1
    assert result.capped[0].server == "s1"


# ── CLI integration ────────────────────────────────────────────────────────

@pytest.fixture()
def config_file(tmp_path):
    content = """servers:
  - name: web
    jobs:
      - name: heartbeat
        schedule: "* * * * *"
        command: curl localhost
      - name: daily-backup
        schedule: "0 2 * * *"
        command: backup.sh
"""
    p = tmp_path / "cron.yaml"
    p.write_text(content)
    return str(p)


def _run(argv):
    from cronwarden.cli_capper import run_cap
    return run_cap(argv)


def test_run_cap_exits_zero_for_clean_config(tmp_path):
    content = "servers:\n  - name: s\n    jobs:\n      - name: j\n        schedule: \"0 6 * * *\"\n        command: echo hi\n"
    p = tmp_path / "c.yaml"
    p.write_text(content)
    assert _run([str(p)]) == 0


def test_run_cap_exits_zero_with_capped_but_no_flag(config_file):
    assert _run([config_file]) == 0


def test_run_cap_exits_one_when_fail_flag_set(config_file):
    assert _run([config_file, "--fail-on-capped"]) == 1


def test_run_cap_json_output_is_valid(config_file, capsys):
    _run([config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "over_capped" in data
    assert "total" in data


def test_run_cap_bad_config_exits_one():
    assert _run(["/nonexistent/path.yaml"]) == 1
