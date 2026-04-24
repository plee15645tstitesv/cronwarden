import pytest
from cronwarden.sorter import sort_config, SortResult, SortedJob, VALID_DIMENSIONS
from cronwarden.config import Config, Server, CronJob


def _make_job(name: str, schedule: str = "0 * * * *", command: str = "echo hi") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config() -> Config:
    server_a = Server(
        name="alpha",
        jobs=[
            _make_job("zebra-task", "0 2 * * *", "zbackup"),
            _make_job("apple-task", "*/5 * * * *", "acheck"),
        ],
    )
    server_b = Server(
        name="beta",
        jobs=[
            _make_job("mango-task", "0 1 * * *", "mrun"),
        ],
    )
    return Config(servers=[server_a, server_b])


def test_sort_config_returns_sort_result():
    config = _make_config()
    result = sort_config(config)
    assert isinstance(result, SortResult)


def test_sort_config_total_matches_all_jobs():
    config = _make_config()
    result = sort_config(config)
    assert result.total() == 3


def test_sort_by_name_ascending():
    config = _make_config()
    result = sort_config(config, dimension="name", reverse=False)
    names = [sj.job.name for sj in result.jobs]
    assert names == sorted(names)


def test_sort_by_name_descending():
    config = _make_config()
    result = sort_config(config, dimension="name", reverse=True)
    names = [sj.job.name for sj in result.jobs]
    assert names == sorted(names, reverse=True)


def test_sort_by_server():
    config = _make_config()
    result = sort_config(config, dimension="server")
    servers = [sj.server for sj in result.jobs]
    assert servers == sorted(servers)


def test_sort_by_command():
    config = _make_config()
    result = sort_config(config, dimension="command")
    commands = [sj.job.command for sj in result.jobs]
    assert commands == sorted(commands)


def test_sort_by_schedule():
    config = _make_config()
    result = sort_config(config, dimension="schedule")
    schedules = [sj.job.schedule for sj in result.jobs]
    assert schedules == sorted(schedules)


def test_invalid_dimension_falls_back_to_name():
    config = _make_config()
    result = sort_config(config, dimension="nonexistent")
    assert result.dimension == "name"
    names = [sj.job.name for sj in result.jobs]
    assert names == sorted(names)


def test_sorted_job_summary_contains_server_and_name():
    config = _make_config()
    result = sort_config(config)
    for sj in result.jobs:
        s = sj.summary()
        assert sj.server in s
        assert sj.job.name in s


def test_is_empty_false_when_jobs_present():
    config = _make_config()
    result = sort_config(config)
    assert not result.is_empty()


def test_is_empty_true_for_empty_config():
    config = Config(servers=[])
    result = sort_config(config)
    assert result.is_empty()


def test_reverse_flag_stored_in_result():
    config = _make_config()
    result = sort_config(config, reverse=True)
    assert result.reverse is True
