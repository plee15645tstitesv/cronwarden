import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.recommender import recommend


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


def test_integration_well_configured_job_has_no_recommendations():
    server = _server("prod", [
        _job("backup", "0 3 * * *", "/usr/bin/backup.sh",
             description="Daily backup", tags=["backup"]),
    ])
    result = recommend(Config(servers=[server]))
    assert not result.has_recommendations


def test_integration_every_minute_flagged_r001():
    server = _server("prod", [
        _job("poller", "* * * * *", "/usr/bin/poll.sh",
             description="Polls API", tags=["monitoring"]),
    ])
    result = recommend(Config(servers=[server]))
    codes = {r.code for r in result.recommendations}
    assert "R001" in codes


def test_integration_sudo_flagged_r002():
    server = _server("prod", [
        _job("cleaner", "0 1 * * *", "sudo rm -rf /tmp/*",
             description="Cleanup", tags=["cleanup"]),
    ])
    result = recommend(Config(servers=[server]))
    codes = {r.code for r in result.recommendations}
    assert "R002" in codes


def test_integration_missing_tags_and_description():
    server = _server("staging", [
        _job("mystery", "30 * * * *", "/opt/run.sh"),
    ])
    result = recommend(Config(servers=[server]))
    codes = {r.code for r in result.recommendations}
    assert "R003" in codes
    assert "R004" in codes


def test_integration_multi_server_aggregates_all():
    servers = [
        _server("s1", [_job("j1", "* * * * *", "/bin/run")]),
        _server("s2", [_job("j2", "* * * * *", "/bin/run")]),
    ]
    result = recommend(Config(servers=servers))
    server_names = {r.server for r in result.recommendations}
    assert "s1" in server_names
    assert "s2" in server_names
