"""Tests for cronwarden.mirrorer."""
import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.mirrorer import mirror_jobs, MirrorResult, MirroredJob


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup.sh", tags=None):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [])


def _make_config():
    server_a = Server(name="alpha", jobs=[
        _make_job("backup", "0 2 * * *", "/backup.sh"),
        _make_job("cleanup", "0 3 * * 0", "/cleanup.sh"),
    ])
    server_b = Server(name="beta", jobs=[
        _make_job("monitor", "*/5 * * * *", "/monitor.sh"),
    ])
    return Config(servers=[server_a, server_b])


def test_mirror_jobs_returns_mirror_result():
    config = _make_config()
    result = mirror_jobs(config, "alpha", "beta")
    assert isinstance(result, MirrorResult)


def test_mirror_jobs_has_mirrored_true_when_jobs_exist():
    config = _make_config()
    result = mirror_jobs(config, "alpha", "beta")
    assert result.has_mirrored is True


def test_mirror_jobs_total_matches_source_jobs():
    config = _make_config()
    result = mirror_jobs(config, "alpha", "beta")
    assert result.total == 2


def test_mirror_jobs_records_source_and_target():
    config = _make_config()
    result = mirror_jobs(config, "alpha", "beta")
    assert result.source_server == "alpha"
    assert result.target_server == "beta"


def test_mirrored_job_fields_are_correct():
    config = _make_config()
    result = mirror_jobs(config, "alpha", "beta")
    names = [m.job_name for m in result.mirrored]
    assert "backup" in names
    assert "cleanup" in names


def test_mirror_jobs_name_filter_reduces_results():
    config = _make_config()
    result = mirror_jobs(config, "alpha", "beta", name_filter="backup")
    assert result.total == 1
    assert result.mirrored[0].job_name == "backup"


def test_mirror_jobs_filter_no_match_returns_empty():
    config = _make_config()
    result = mirror_jobs(config, "alpha", "beta", name_filter="zzznomatch")
    assert result.has_mirrored is False
    assert result.total == 0


def test_mirror_jobs_raises_for_missing_source():
    config = _make_config()
    with pytest.raises(ValueError, match="Source server"):
        mirror_jobs(config, "nonexistent", "beta")


def test_mirror_jobs_raises_for_missing_target():
    config = _make_config()
    with pytest.raises(ValueError, match="Target server"):
        mirror_jobs(config, "alpha", "nonexistent")


def test_mirrored_job_summary_contains_names():
    m = MirroredJob(
        source_server="alpha",
        target_server="beta",
        job_name="backup",
        schedule="0 2 * * *",
        command="/backup.sh",
    )
    s = m.summary()
    assert "backup" in s
    assert "alpha" in s
    assert "beta" in s
