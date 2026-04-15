"""Notification support for cronwarden audit results."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.auditor import audit_config
from cronwarden.config import Config


@dataclass
class NotificationChannel:
    type: str  # 'slack', 'email', 'webhook'
    target: str  # URL or address
    on_failure_only: bool = True


@dataclass
class NotificationResult:
    channel: NotificationChannel
    success: bool
    message: str = ""

    def __str__(self) -> str:
        status = "sent" if self.success else "failed"
        return f"[{self.channel.type}] {status}: {self.message}"


def _build_payload(config: Config, failure_count: int, total: int) -> dict:
    """Build a generic notification payload dict."""
    return {
        "tool": "cronwarden",
        "summary": f"{failure_count} failure(s) found in {total} job(s)",
        "failure_count": failure_count,
        "total_jobs": total,
        "servers": [s.name for s in config.servers],
    }


def _send_webhook(url: str, payload: dict) -> NotificationResult:
    """Send a webhook notification (simulated for testability)."""
    import json
    try:
        import urllib.request
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5)
        return NotificationResult(channel=NotificationChannel(type="webhook", target=url), success=True, message="OK")
    except Exception as exc:
        return NotificationResult(
            channel=NotificationChannel(type="webhook", target=url),
            success=False,
            message=str(exc),
        )


def notify(config: Config, channels: List[NotificationChannel]) -> List[NotificationResult]:
    """Run audit and dispatch notifications to all channels."""
    server_reports = audit_config(config)
    total = sum(len(r.job_reports) for r in server_reports)
    failures = sum(
        1 for r in server_reports for jr in r.job_reports if not jr.result.is_valid
    )
    results = []
    for channel in channels:
        if channel.on_failure_only and failures == 0:
            results.append(NotificationResult(channel=channel, success=True, message="skipped (no failures)"))
            continue
        payload = _build_payload(config, failures, total)
        if channel.type == "webhook":
            results.append(_send_webhook(channel.target, payload))
        else:
            results.append(NotificationResult(channel=channel, success=False, message=f"unsupported channel type: {channel.type}"))
    return results
