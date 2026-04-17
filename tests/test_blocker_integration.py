"""Integration tests for blocker using realistic config structures."""
import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.blocker import find_conflicts


def _job(name, schedule, tags=None):
    return CronJob(
        name=name,
        schedule=schedule,
        command=f"/usr/bin/{name}",
        description=f"{name} job",
        tags=tags or [],
    )


def test_integration_no_conflicts_in_well_spread_config():
    server = Server(
        name="prod",
        host="prod.example.com",
        jobs=[
            _job("daily_backup", "0 1 * * *"),
            _job("weekly_report", "0 6 * * 0"),
            _job("hourly_sync", "0 * * * *"),
            _job("nightly_cleanup", "0 3 * * *"),
        ],
    )
    config = Config(servers=[server])
    result = find_conflicts(config)
    assert not result.has_conflicts


def test_integration_detects_conflict_in_dense_schedule():
    server = Server(
        name="staging",
        host="staging.example.com",
        jobs=[
            _job("job_x", "*/10 * * * *"),
            _job("job_y", "*/10 * * * *"),
        ],
    )
    config = Config(servers=[server])
    result = find_conflicts(config)
    assert result.has_conflicts
    assert result.pairs[0].reason == "identical schedule expression"


def test_integration_multiple_servers_isolated():
    s1 = Server(name="s1", host="s1.example.com", jobs=[
        _job("sync", "0 4 * * *"),
    ])
    s2 = Server(name="s2", host="s2.example.com", jobs=[
        _job("sync", "0 4 * * *"),
    ])
    config = Config(servers=[s1, s2])
    result = find_conflicts(config)
    assert not result.has_conflicts
