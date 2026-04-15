"""Tests for cronwarden.notifier."""

import pytest
from unittest.mock import patch, MagicMock
from cronwarden.notifier import (
    NotificationChannel,
    NotificationResult,
    notify,
    _build_payload,
)
from cronwarden.config import Config, Server, CronJob


def _make_job(name="backup", schedule="0 2 * * *", tags=None):
    return CronJob(name=name, schedule=schedule, command="/usr/bin/backup", tags=tags or [])


def _make_config(jobs=None, server_name="prod"):
    job_list = jobs if jobs is not None else [_make_job()]
    server = Server(name=server_name, host="localhost", jobs=job_list)
    return Config(servers=[server])


def test_notification_channel_defaults():
    ch = NotificationChannel(type="webhook", target="http://example.com")
    assert ch.on_failure_only is True


def test_notification_result_str_success():
    ch = NotificationChannel(type="slack", target="http://hooks.slack.com/x")
    r = NotificationResult(channel=ch, success=True, message="OK")
    assert "sent" in str(r)
    assert "slack" in str(r)


def test_notification_result_str_failure():
    ch = NotificationChannel(type="email", target="ops@example.com")
    r = NotificationResult(channel=ch, success=False, message="timeout")
    assert "failed" in str(r)


def test_build_payload_keys():
    config = _make_config()
    payload = _build_payload(config, failure_count=1, total=3)
    assert payload["tool"] == "cronwarden"
    assert payload["failure_count"] == 1
    assert payload["total_jobs"] == 3
    assert "prod" in payload["servers"]


def test_notify_skips_when_no_failures_and_on_failure_only():
    config = _make_config(jobs=[_make_job(schedule="0 2 * * *")])
    ch = NotificationChannel(type="webhook", target="http://example.com", on_failure_only=True)
    results = notify(config, [ch])
    assert len(results) == 1
    assert results[0].success is True
    assert "skipped" in results[0].message


def test_notify_sends_when_on_failure_only_false():
    config = _make_config(jobs=[_make_job(schedule="0 2 * * *")])
    ch = NotificationChannel(type="webhook", target="http://example.com", on_failure_only=False)
    with patch("cronwarden.notifier._send_webhook") as mock_send:
        mock_send.return_value = NotificationResult(channel=ch, success=True, message="OK")
        results = notify(config, [ch])
    mock_send.assert_called_once()
    assert results[0].success is True


def test_notify_unsupported_channel_type():
    config = _make_config(jobs=[_make_job(schedule="bad-schedule")])
    ch = NotificationChannel(type="sms", target="+15551234567", on_failure_only=False)
    results = notify(config, [ch])
    assert results[0].success is False
    assert "unsupported" in results[0].message


def test_notify_returns_result_per_channel():
    config = _make_config()
    channels = [
        NotificationChannel(type="webhook", target="http://a.com", on_failure_only=False),
        NotificationChannel(type="webhook", target="http://b.com", on_failure_only=False),
    ]
    with patch("cronwarden.notifier._send_webhook") as mock_send:
        mock_send.return_value = NotificationResult(
            channel=channels[0], success=True, message="OK"
        )
        results = notify(config, channels)
    assert len(results) == 2
