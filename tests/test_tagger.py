"""Tests for cronwarden.tagger."""

import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.tagger import filter_by_tag, list_all_tags, TagFilterResult


def _make_job(name: str, tags=None) -> CronJob:
    return CronJob(
        name=name,
        schedule="0 * * * *",
        command=f"echo {name}",
        description=None,
        tags=tags or [],
    )


def _make_config() -> Config:
    server_a = Server(
        name="web-01",
        host="web01.example.com",
        jobs=[
            _make_job("backup", tags=["backup", "nightly"]),
            _make_job("cleanup", tags=["maintenance"]),
            _make_job("report", tags=["nightly"]),
        ],
    )
    server_b = Server(
        name="db-01",
        host="db01.example.com",
        jobs=[
            _make_job("db-backup", tags=["backup", "critical"]),
            _make_job("health-check", tags=["monitoring"]),
        ],
    )
    return Config(servers=[server_a, server_b])


def test_filter_by_tag_returns_tag_filter_result():
    config = _make_config()
    result = filter_by_tag(config, "backup")
    assert isinstance(result, TagFilterResult)


def test_filter_by_tag_matches_correct_jobs():
    config = _make_config()
    result = filter_by_tag(config, "backup")
    assert result.matched_jobs == 2


def test_filter_by_tag_includes_correct_servers():
    config = _make_config()
    result = filter_by_tag(config, "backup")
    server_names = [s.name for s in result.matched_servers]
    assert "web-01" in server_names
    assert "db-01" in server_names


def test_filter_by_tag_excludes_non_matching_jobs():
    config = _make_config()
    result = filter_by_tag(config, "nightly")
    assert result.matched_jobs == 2
    assert len(result.matched_servers) == 1
    assert result.matched_servers[0].name == "web-01"


def test_filter_by_tag_case_insensitive():
    config = _make_config()
    result = filter_by_tag(config, "BACKUP")
    assert result.matched_jobs == 2


def test_filter_by_tag_no_matches():
    config = _make_config()
    result = filter_by_tag(config, "nonexistent")
    assert result.has_matches is False
    assert result.matched_jobs == 0
    assert result.matched_servers == []


def test_filter_by_tag_total_jobs_counts_all():
    config = _make_config()
    result = filter_by_tag(config, "backup")
    assert result.total_jobs == 5


def test_list_all_tags_returns_sorted_unique():
    config = _make_config()
    tags = list_all_tags(config)
    assert tags == sorted(set(tags))
    assert "backup" in tags
    assert "nightly" in tags
    assert "critical" in tags
    assert "maintenance" in tags
    assert "monitoring" in tags


def test_list_all_tags_no_duplicates():
    config = _make_config()
    tags = list_all_tags(config)
    assert len(tags) == len(set(tags))


def test_list_all_tags_empty_config():
    config = Config(servers=[])
    assert list_all_tags(config) == []
