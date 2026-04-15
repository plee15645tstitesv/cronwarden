"""Tests for cronwarden.grouper."""

import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.grouper import (
    GroupedJobs,
    group_by_tag,
    group_by_server,
    group_by_frequency,
    _frequency_label,
)


def _make_job(name, schedule="0 * * * *", tags=None, description=None):
    return CronJob(name=name, schedule=schedule, command=f"run-{name}",
                   description=description, tags=tags or [])


def _make_config():
    server_a = Server(
        name="web-01",
        host="web-01.example.com",
        jobs=[
            _make_job("backup", schedule="0 2 * * *", tags=["backup", "nightly"]),
            _make_job("cleanup", schedule="@daily", tags=["maintenance"]),
        ],
    )
    server_b = Server(
        name="db-01",
        host="db-01.example.com",
        jobs=[
            _make_job("dump", schedule="0 3 * * 0", tags=["backup"]),
            _make_job("health", schedule="* * * * *"),
        ],
    )
    return Config(servers=[server_a, server_b])


def test_group_by_tag_returns_grouped_jobs():
    result = group_by_tag(_make_config())
    assert isinstance(result, GroupedJobs)
    assert result.dimension == "tag"


def test_group_by_tag_collects_shared_tags():
    result = group_by_tag(_make_config())
    assert "backup" in result.group_names()
    assert len(result.jobs_in_group("backup")) == 2


def test_group_by_tag_untagged_jobs():
    result = group_by_tag(_make_config())
    assert "untagged" in result.group_names()
    assert len(result.jobs_in_group("untagged")) == 1


def test_group_by_server_returns_grouped_jobs():
    result = group_by_server(_make_config())
    assert isinstance(result, GroupedJobs)
    assert result.dimension == "server"


def test_group_by_server_has_correct_groups():
    result = group_by_server(_make_config())
    assert set(result.group_names()) == {"web-01", "db-01"}


def test_group_by_server_counts_jobs_per_server():
    result = group_by_server(_make_config())
    assert len(result.jobs_in_group("web-01")) == 2
    assert len(result.jobs_in_group("db-01")) == 2


def test_group_by_frequency_returns_grouped_jobs():
    result = group_by_frequency(_make_config())
    assert isinstance(result, GroupedJobs)
    assert result.dimension == "frequency"


def test_group_by_frequency_detects_daily():
    result = group_by_frequency(_make_config())
    assert "daily" in result.group_names()


def test_group_by_frequency_detects_every_minute():
    result = group_by_frequency(_make_config())
    assert "every-minute" in result.group_names()


def test_total_jobs_counts_all():
    result = group_by_server(_make_config())
    assert result.total_jobs() == 4


def test_is_empty_false_when_jobs_exist():
    result = group_by_server(_make_config())
    assert not result.is_empty()


def test_is_empty_true_for_empty_config():
    empty = Config(servers=[])
    result = group_by_server(empty)
    assert result.is_empty()


@pytest.mark.parametrize("schedule,expected", [
    ("@yearly", "yearly"),
    ("@monthly", "monthly"),
    ("@weekly", "weekly"),
    ("@daily", "daily"),
    ("@midnight", "daily"),
    ("@hourly", "hourly"),
    ("@reboot", "reboot"),
    ("* * * * *", "every-minute"),
    ("0 * * * *", "hourly"),
    ("0 2 * * *", "daily"),
    ("0 3 * * 0", "weekly"),
    ("0 1 1 * *", "monthly"),
])
def test_frequency_label(schedule, expected):
    assert _frequency_label(schedule) == expected
