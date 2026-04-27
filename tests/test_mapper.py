"""Tests for cronwarden/mapper.py"""

import pytest
from cronwarden.mapper import map_config, MapEntry, MapResult
from cronwarden.config import Config, Server, CronJob


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup", tags=None):
    return CronJob(
        name=name,
        schedule=schedule,
        command=command,
        description=None,
        tags=tags or [],
    )


def _make_config(*server_job_pairs):
    servers = []
    for sname, jobs in server_job_pairs:
        servers.append(Server(name=sname, host=f"{sname}.example.com", jobs=list(jobs)))
    return Config(servers=servers)


def test_map_config_returns_map_result():
    config = _make_config(("web", [_make_job()]))
    result = map_config(config)
    assert isinstance(result, MapResult)


def test_map_config_total_matches_all_jobs():
    config = _make_config(
        ("web", [_make_job("a"), _make_job("b")]),
        ("db", [_make_job("c")]),
    )
    result = map_config(config)
    assert result.total == 3


def test_map_config_is_empty_false_when_jobs_exist():
    config = _make_config(("web", [_make_job()]))
    result = map_config(config)
    assert not result.is_empty


def test_map_config_is_empty_true_when_no_jobs():
    config = Config(servers=[])
    result = map_config(config)
    assert result.is_empty


def test_map_config_servers_list():
    config = _make_config(
        ("alpha", [_make_job()]),
        ("beta", [_make_job()]),
    )
    result = map_config(config)
    assert set(result.servers()) == {"alpha", "beta"}


def test_jobs_for_server_returns_correct_entries():
    config = _make_config(
        ("web", [_make_job("job1"), _make_job("job2")]),
        ("db", [_make_job("job3")]),
    )
    result = map_config(config)
    web_jobs = result.jobs_for_server("web")
    assert len(web_jobs) == 2
    assert all(isinstance(e, MapEntry) for e in web_jobs)


def test_entry_fields_are_populated():
    job = _make_job(name="nightly", schedule="0 3 * * *", command="/bin/run", tags=["backup"])
    config = _make_config(("srv", [job]))
    result = map_config(config)
    entry = result.entries[0]
    assert entry.server == "srv"
    assert entry.job_name == "nightly"
    assert entry.schedule == "0 3 * * *"
    assert entry.command == "/bin/run"
    assert entry.tags == ["backup"]


def test_filter_by_tag_excludes_non_matching():
    job_a = _make_job("a", tags=["backup"])
    job_b = _make_job("b", tags=["cleanup"])
    config = _make_config(("web", [job_a, job_b]))
    result = map_config(config, tag="backup")
    assert result.total == 1
    assert result.entries[0].job_name == "a"


def test_filter_by_tag_empty_when_no_match():
    job = _make_job("a", tags=["monitor"])
    config = _make_config(("web", [job]))
    result = map_config(config, tag="backup")
    assert result.is_empty


def test_entry_summary_contains_server_and_name():
    entry = MapEntry(server="web", job_name="nightly", schedule="@daily", command="/bin/run", tags=["backup"])
    s = entry.summary()
    assert "web" in s
    assert "nightly" in s


def test_server_with_no_matching_tags_excluded_from_index():
    job_a = _make_job("a", tags=["backup"])
    job_b = _make_job("b", tags=["cleanup"])
    config = _make_config(
        ("web", [job_a]),
        ("db", [job_b]),
    )
    result = map_config(config, tag="backup")
    assert "db" not in result.servers()
    assert "web" in result.servers()
