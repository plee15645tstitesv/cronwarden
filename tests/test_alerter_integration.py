import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.alerter import check_alerts


def _job(name, schedule, command, description=None, tags=None):
    return CronJob(
        name=name,
        schedule=schedule,
        command=command,
        description=description,
        tags=tags or [],
    )


def _server(name, jobs):
    return Server(name=name, jobs=jobs)


def test_integration_clean_config_has_no_alerts():
    config = Config(servers=[
        _server("web-01", [
            _job("backup", "0 2 * * *", "/usr/bin/backup.sh", "Nightly backup"),
            _job("cleanup", "0 3 * * 0", "/usr/bin/cleanup.sh", "Weekly cleanup"),
        ])
    ])
    result = check_alerts(config)
    assert not result.has_alerts


def test_integration_multiple_violations_detected():
    config = Config(servers=[
        _server("web-01", [
            _job("bad", "not-valid", "sudo rm -rf /"),
        ])
    ])
    result = check_alerts(config)
    levels = {a.level for a in result.alerts}
    assert "critical" in levels
    assert "warning" in levels


def test_integration_critical_filter_excludes_warnings():
    config = Config(servers=[
        _server("web-01", [
            _job("warn-job", "* * * * *", "/usr/bin/ok.sh"),
        ])
    ])
    result = check_alerts(config, level_filter="critical")
    assert all(a.level == "critical" for a in result.alerts)


def test_integration_alerts_carry_correct_server_name():
    config = Config(servers=[
        _server("db-primary", [
            _job("broken", "bad-schedule", "/usr/bin/broken.sh"),
        ])
    ])
    result = check_alerts(config)
    assert all(a.server == "db-primary" for a in result.alerts)
