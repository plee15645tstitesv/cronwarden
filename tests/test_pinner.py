"""Tests for cronwarden.pinner and cronwarden.cli_pin."""

import json
import pytest
from unittest.mock import patch

from cronwarden.pinner import PinnedJob, PinResult, check_pins
from cronwarden.cli_pin import _parse_pin_args, run_pin
from cronwarden.config import Config, Server, CronJob


def _make_job(name: str, schedule: str = "0 * * * *") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=f"echo {name}")


def _make_config() -> Config:
    return Config(
        servers=[
            Server(
                name="web",
                host="web.example.com",
                jobs=[
                    _make_job("backup", "0 2 * * *"),
                    _make_job("cleanup", "30 3 * * 0"),
                ],
            ),
            Server(
                name="db",
                host="db.example.com",
                jobs=[_make_job("dump", "0 1 * * *")],
            ),
        ]
    )


# --- PinnedJob ---

def test_pinned_job_no_drift():
    p = PinnedJob(server="web", job_name="backup", expected_schedule="0 2 * * *", actual_schedule="0 2 * * *")
    assert not p.has_drifted


def test_pinned_job_drift_detected():
    p = PinnedJob(server="web", job_name="backup", expected_schedule="0 2 * * *", actual_schedule="0 3 * * *")
    assert p.has_drifted


def test_pinned_job_summary_ok():
    p = PinnedJob(server="web", job_name="backup", expected_schedule="0 2 * * *", actual_schedule="0 2 * * *")
    assert "[OK]" in p.summary()
    assert "backup" in p.summary()


def test_pinned_job_summary_drift():
    p = PinnedJob(server="web", job_name="backup", expected_schedule="0 2 * * *", actual_schedule="0 3 * * *")
    assert "[DRIFT]" in p.summary()


# --- PinResult ---

def test_pin_result_empty_has_no_drift():
    r = PinResult()
    assert not r.has_drift
    assert r.total == 0
    assert r.drift_count == 0


def test_pin_result_counts_drift():
    r = PinResult(pins=[
        PinnedJob("web", "backup", "0 2 * * *", "0 2 * * *"),
        PinnedJob("web", "cleanup", "0 3 * * *", "30 3 * * *"),
    ])
    assert r.has_drift
    assert r.drift_count == 1
    assert r.total == 2


# --- check_pins ---

def test_check_pins_no_drift():
    config = _make_config()
    result = check_pins(config, {"web": {"backup": "0 2 * * *"}})
    assert result.total == 1
    assert not result.has_drift


def test_check_pins_detects_drift():
    config = _make_config()
    result = check_pins(config, {"web": {"backup": "0 5 * * *"}})
    assert result.has_drift
    assert result.drifted[0].job_name == "backup"


def test_check_pins_missing_job_shows_missing():
    config = _make_config()
    result = check_pins(config, {"web": {"nonexistent": "0 1 * * *"}})
    assert result.pins[0].actual_schedule == "<missing>"
    assert result.has_drift


def test_check_pins_empty_pins_returns_empty():
    config = _make_config()
    result = check_pins(config, {})
    assert result.total == 0


# --- _parse_pin_args ---

def test_parse_pin_args_valid():
    pins = _parse_pin_args(["web/backup=0 2 * * *", "db/dump=0 1 * * *"])
    assert pins["web"]["backup"] == "0 2 * * *"
    assert pins["db"]["dump"] == "0 1 * * *"


def test_parse_pin_args_invalid_format():
    with pytest.raises(ValueError, match="Invalid pin format"):
        _parse_pin_args(["bad-format"])


# --- run_pin CLI ---

@pytest.fixture
def config_file(tmp_path):
    f = tmp_path / "crons.yml"
    f.write_text(
        "servers:\n"
        "  - name: web\n"
        "    host: web.example.com\n"
        "    jobs:\n"
        "      - name: backup\n"
        "        schedule: '0 2 * * *'\n"
        "        command: /usr/bin/backup.sh\n"
    )
    return str(f)


def test_run_pin_exits_zero_no_drift(config_file):
    code = run_pin([config_file, "--pin", "web/backup=0 2 * * *"])
    assert code == 0


def test_run_pin_exits_zero_with_drift_without_flag(config_file):
    code = run_pin([config_file, "--pin", "web/backup=0 9 * * *"])
    assert code == 0


def test_run_pin_exits_one_with_drift_and_flag(config_file):
    code = run_pin([config_file, "--pin", "web/backup=0 9 * * *", "--fail-on-drift"])
    assert code == 1


def test_run_pin_json_output_is_valid(config_file, capsys):
    run_pin([config_file, "--pin", "web/backup=0 2 * * *", "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "pins" in data
    assert data["total"] == 1
