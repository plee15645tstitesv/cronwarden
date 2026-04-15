"""Integration tests: notifier + auditor + config pipeline."""

import pytest
from unittest.mock import patch
from cronwarden.config import Config, Server, CronJob
from cronwarden.notifier import NotificationChannel, NotificationResult, notify


def _make_config_with_invalid_job():
    bad_job = CronJob(name="bad", schedule="not-a-cron", command="/bin/bad")
    server = Server(name="staging", host="staging.example.com", jobs=[bad_job])
    return Config(servers=[server])


def _make_config_with_valid_jobs():
    good_job = CronJob(name="backup", schedule="0 2 * * *", command="/bin/backup", description="Daily backup")
    server = Server(name="prod", host="prod.example.com", jobs=[good_job])
    return Config(servers=[server])


def test_notify_triggers_on_invalid_job_via_webhook():
    config = _make_config_with_invalid_job()
    ch = NotificationChannel(type="webhook", target="http://hooks.example.com/cron", on_failure_only=True)
    with patch("cronwarden.notifier._send_webhook") as mock_send:
        mock_send.return_value = NotificationResult(channel=ch, success=True, message="delivered")
        results = notify(config, [ch])
    mock_send.assert_called_once()
    payload = mock_send.call_args[0][1]
    assert payload["failure_count"] >= 1


def test_notify_does_not_trigger_for_valid_jobs_when_on_failure_only():
    config = _make_config_with_valid_jobs()
    ch = NotificationChannel(type="webhook", target="http://hooks.example.com/cron", on_failure_only=True)
    with patch("cronwarden.notifier._send_webhook") as mock_send:
        results = notify(config, [ch])
    mock_send.assert_not_called()
    assert "skipped" in results[0].message


def test_notify_multiple_channels_all_called():
    config = _make_config_with_invalid_job()
    channels = [
        NotificationChannel(type="webhook", target="http://a.example.com", on_failure_only=True),
        NotificationChannel(type="webhook", target="http://b.example.com", on_failure_only=True),
    ]
    with patch("cronwarden.notifier._send_webhook") as mock_send:
        mock_send.side_effect = [
            NotificationResult(channel=channels[0], success=True, message="OK"),
            NotificationResult(channel=channels[1], success=True, message="OK"),
        ]
        results = notify(config, channels)
    assert mock_send.call_count == 2
    assert all(r.success for r in results)


def test_notify_payload_includes_server_name():
    config = _make_config_with_invalid_job()
    ch = NotificationChannel(type="webhook", target="http://x.com", on_failure_only=False)
    with patch("cronwarden.notifier._send_webhook") as mock_send:
        mock_send.return_value = NotificationResult(channel=ch, success=True, message="OK")
        notify(config, [ch])
    payload = mock_send.call_args[0][1]
    assert "staging" in payload["servers"]
