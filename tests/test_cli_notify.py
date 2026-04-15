"""Tests for cronwarden.cli_notify."""

import json
import pytest
from unittest.mock import patch
from cronwarden.cli_notify import run_notify, _parse_channels
from cronwarden.notifier import NotificationChannel, NotificationResult


@pytest.fixture
def config_file(tmp_path):
    content = """
servers:
  - name: web
    host: web01.example.com
    jobs:
      - name: cleanup
        schedule: "0 3 * * *"
        command: /usr/bin/cleanup
        description: Nightly cleanup
"""
    p = tmp_path / "cronwarden.yml"
    p.write_text(content)
    return str(p)


def test_parse_channels_valid():
    channels = _parse_channels(["webhook:http://example.com"])
    assert len(channels) == 1
    assert channels[0].type == "webhook"
    assert channels[0].target == "http://example.com"


def test_parse_channels_invalid_format():
    with pytest.raises(ValueError, match="Invalid channel format"):
        _parse_channels(["nocolon"])


def test_run_notify_no_channels_exits_one(config_file):
    result = run_notify([config_file])
    assert result == 1


def test_run_notify_bad_config_exits_one(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("not: valid: cron: config")
    result = run_notify([str(bad), "--channel", "webhook:http://x.com"])
    assert result == 1


def test_run_notify_returns_zero_on_success(config_file):
    ch = NotificationChannel(type="webhook", target="http://ok.com", on_failure_only=False)
    mock_result = NotificationResult(channel=ch, success=True, message="OK")
    with patch("cronwarden.cli_notify.notify", return_value=[mock_result]):
        result = run_notify([config_file, "--channel", "webhook:http://ok.com", "--always"])
    assert result == 0


def test_run_notify_returns_one_on_failure(config_file):
    ch = NotificationChannel(type="webhook", target="http://fail.com")
    mock_result = NotificationResult(channel=ch, success=False, message="timeout")
    with patch("cronwarden.cli_notify.notify", return_value=[mock_result]):
        result = run_notify([config_file, "--channel", "webhook:http://fail.com"])
    assert result == 1


def test_run_notify_json_output_is_valid(config_file, capsys):
    ch = NotificationChannel(type="webhook", target="http://ok.com", on_failure_only=False)
    mock_result = NotificationResult(channel=ch, success=True, message="OK")
    with patch("cronwarden.cli_notify.notify", return_value=[mock_result]):
        run_notify([config_file, "--channel", "webhook:http://ok.com", "--always", "--json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["success"] is True
