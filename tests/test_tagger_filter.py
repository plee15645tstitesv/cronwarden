"""Tests for cronwarden.tagger_filter."""
import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.tagger_filter import (
    TagFilteredResult,
    TagFilteredServer,
    filter_config_by_tags,
)


def _make_job(name: str, tags=None, schedule="0 * * * *", command="echo hi"):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [])


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def _make_server(name: str, *jobs: CronJob) -> Server:
    return Server(name=name, jobs=list(jobs))


def test_filter_returns_tag_filtered_result():
    config = _make_config(_make_server("web", _make_job("j1", tags=["backup"])))
    result = filter_config_by_tags(config, ["backup"])
    assert isinstance(result, TagFilteredResult)


def test_has_matches_true_when_jobs_match():
    config = _make_config(_make_server("web", _make_job("j1", tags=["backup"])))
    result = filter_config_by_tags(config, ["backup"])
    assert result.has_matches is True


def test_has_matches_false_when_no_jobs_match():
    config = _make_config(_make_server("web", _make_job("j1", tags=["cleanup"])))
    result = filter_config_by_tags(config, ["backup"])
    assert result.has_matches is False


def test_total_matched_counts_correctly():
    server = _make_server(
        "web",
        _make_job("j1", tags=["backup"]),
        _make_job("j2", tags=["backup"]),
        _make_job("j3", tags=["cleanup"]),
    )
    config = _make_config(server)
    result = filter_config_by_tags(config, ["backup"])
    assert result.total_matched == 2


def test_matched_server_names_excludes_empty_servers():
    s1 = _make_server("web", _make_job("j1", tags=["backup"]))
    s2 = _make_server("db", _make_job("j2", tags=["cleanup"]))
    config = _make_config(s1, s2)
    result = filter_config_by_tags(config, ["backup"])
    assert "web" in result.matched_server_names
    assert "db" not in result.matched_server_names


def test_require_all_matches_only_jobs_with_all_tags():
    server = _make_server(
        "web",
        _make_job("j1", tags=["backup", "daily"]),
        _make_job("j2", tags=["backup"]),
    )
    config = _make_config(server)
    result = filter_config_by_tags(config, ["backup", "daily"], require_all=True)
    assert result.total_matched == 1
    assert result.servers[0].matched_jobs[0].name == "j1"


def test_tag_matching_is_case_insensitive():
    config = _make_config(_make_server("web", _make_job("j1", tags=["Backup"])))
    result = filter_config_by_tags(config, ["backup"])
    assert result.has_matches is True


def test_server_summary_line():
    server_result = TagFilteredServer(
        server_name="prod",
        matched_jobs=[_make_job("j1"), _make_job("j2")],
    )
    assert "prod" in server_result.summary()
    assert "2" in server_result.summary()


def test_empty_config_returns_no_matches():
    config = _make_config()
    result = filter_config_by_tags(config, ["backup"])
    assert result.has_matches is False
    assert result.total_matched == 0


def test_job_with_no_tags_never_matches():
    config = _make_config(_make_server("web", _make_job("j1", tags=[])))
    result = filter_config_by_tags(config, ["backup"])
    assert result.has_matches is False
