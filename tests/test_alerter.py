import pytest
from cronwarden.alerter import check_alerts, Alert, AlertResult, _check_job
from cronwarden.config import CronJob, Server, Config


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup.sh",
              description="Nightly backup", tags=None):
    return CronJob(
        name=name,
        schedule=schedule,
        command=command,
        description=description,
        tags=tags or [],
    )


def _make_config(jobs_by_server=None):
    if jobs_by_server is None:
        jobs_by_server = {"web-01": [_make_job()]}
    servers = [
        Server(name=name, jobs=jobs)
        for name, jobs in jobs_by_server.items()
    ]
    return Config(servers=servers)


def test_check_alerts_returns_alert_result():
    config = _make_config()
    result = check_alerts(config)
    assert isinstance(result, AlertResult)


def test_clean_job_has_no_alerts():
    config = _make_config()
    result = check_alerts(config)
    assert not result.has_alerts


def test_invalid_schedule_raises_critical_alert():
    job = _make_job(schedule="not-a-cron")
    config = _make_config({"web-01": [job]})
    result = check_alerts(config)
    assert result.has_alerts
    assert any(a.level == "critical" for a in result.alerts)


def test_sudo_command_raises_warning():
    job = _make_job(command="sudo /usr/bin/cleanup.sh")
    config = _make_config({"web-01": [job]})
    result = check_alerts(config)
    assert any(a.level == "warning" and "sudo" in a.message for a in result.alerts)


def test_every_minute_schedule_raises_warning():
    job = _make_job(schedule="* * * * *")
    config = _make_config({"web-01": [job]})
    result = check_alerts(config)
    assert any(a.level == "warning" and "every minute" in a.message for a in result.alerts)


def test_level_filter_returns_only_matching_level():
    job = _make_job(schedule="not-a-cron", command="sudo do-it")
    config = _make_config({"web-01": [job]})
    result = check_alerts(config, level_filter="critical")
    assert all(a.level == "critical" for a in result.alerts)


def test_alert_summary_format():
    alert = Alert(server="web-01", job_name="backup", level="warning", message="uses sudo")
    assert "WARNING" in alert.summary()
    assert "web-01" in alert.summary()
    assert "backup" in alert.summary()


def test_total_counts_all_alerts():
    job1 = _make_job(name="j1", schedule="not-valid")
    job2 = _make_job(name="j2", command="sudo rm -rf /")
    config = _make_config({"web-01": [job1, job2]})
    result = check_alerts(config)
    assert result.total >= 2


def test_by_level_helper():
    alerts = [
        Alert("s", "j", "critical", "bad schedule"),
        Alert("s", "j", "warning", "sudo"),
    ]
    r = AlertResult(alerts=alerts)
    assert len(r.critical) == 1
    assert len(r.warnings) == 1


def test_multiple_servers_each_checked():
    config = _make_config({
        "web-01": [_make_job(name="j1", schedule="bad")],
        "db-01": [_make_job(name="j2", schedule="also-bad")],
    })
    result = check_alerts(config)
    servers_with_alerts = {a.server for a in result.alerts}
    assert "web-01" in servers_with_alerts
    assert "db-01" in servers_with_alerts
