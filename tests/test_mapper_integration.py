"""Integration tests for mapper: config file -> map_config -> MapResult."""

import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.mapper import map_config


def _job(name, schedule="0 1 * * *", command="/bin/run", tags=None):
    return CronJob(
        name=name,
        schedule=schedule,
        command=command,
        description=None,
        tags=tags or [],
    )


def _server(name, jobs):
    return Server(name=name, host=f"{name}.host", jobs=jobs)


def test_integration_all_jobs_appear_in_result():
    config = Config(servers=[
        _server("web", [_job("a"), _job("b")]),
        _server("db", [_job("c"), _job("d"), _job("e")]),
    ])
    result = map_config(config)
    assert result.total == 5


def test_integration_tag_filter_across_servers():
    config = Config(servers=[
        _server("web", [_job("a", tags=["backup"]), _job("b", tags=["monitor"])]),
        _server("db", [_job("c", tags=["backup"]), _job("d", tags=["cleanup"])]),
    ])
    result = map_config(config, tag="backup")
    assert result.total == 2
    names = {e.job_name for e in result.entries}
    assert names == {"a", "c"}


def test_integration_server_index_correct():
    config = Config(servers=[
        _server("alpha", [_job("x"), _job("y")]),
        _server("beta", [_job("z")]),
    ])
    result = map_config(config)
    assert len(result.jobs_for_server("alpha")) == 2
    assert len(result.jobs_for_server("beta")) == 1


def test_integration_no_jobs_returns_empty():
    config = Config(servers=[])
    result = map_config(config)
    assert result.is_empty
    assert result.total == 0
    assert result.servers() == []
