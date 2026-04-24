import json
import pytest
from cronwarden.cli_alerter import run_alert


@pytest.fixture
def config_file(tmp_path):
    content = """servers:
  - name: web-01
    jobs:
      - name: backup
        schedule: "0 2 * * *"
        command: /usr/bin/backup.sh
        description: Nightly backup
"""
    p = tmp_path / "cronwarden.yaml"
    p.write_text(content)
    return str(p)


@pytest.fixture
def noisy_config_file(tmp_path):
    content = """servers:
  - name: web-01
    jobs:
      - name: risky
        schedule: "* * * * *"
        command: sudo /usr/bin/risky.sh
        description: Risky job
"""
    p = tmp_path / "noisy.yaml"
    p.write_text(content)
    return str(p)


def _run(args):
    return run_alert(args)


def test_run_alert_exits_zero_for_clean_config(config_file):
    assert _run([config_file]) == 0


def test_run_alert_exits_one_for_bad_config(tmp_path):
    missing = str(tmp_path / "nope.yaml")
    assert _run([missing]) == 1


def test_run_alert_json_output_is_valid(config_file, capsys):
    _run([config_file, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)


def test_run_alert_text_contains_no_alerts_message(config_file, capsys):
    _run([config_file])
    captured = capsys.readouterr()
    assert "No alerts" in captured.out


def test_run_alert_noisy_config_shows_warnings(noisy_config_file, capsys):
    _run([noisy_config_file])
    captured = capsys.readouterr()
    assert "WARNING" in captured.out


def test_fail_on_critical_returns_two(tmp_path):
    content = """servers:
  - name: web-01
    jobs:
      - name: broken
        schedule: "not-valid"
        command: /usr/bin/broken.sh
"""
    p = tmp_path / "broken.yaml"
    p.write_text(content)
    assert _run([str(p), "--fail-on-critical"]) == 2


def test_level_filter_passed_through(noisy_config_file, capsys):
    _run([noisy_config_file, "--level", "warning"])
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
