"""Integration tests combining scorer with validator and linter."""
import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.scorer import score_config, _score_job


def _make_job(**kwargs):
    defaults = dict(
        name="sync",
        schedule="*/5 * * * *",
        command="/usr/local/bin/sync",
        description="Sync data",
        tags=["sync"],
    )
    defaults.update(kwargs)
    return CronJob(**defaults)


def _server(jobs):
    return Server(name="prod01", jobs=jobs)


def test_well_configured_job_scores_90_or_above():
    job = _make_job()
    score = _score_job(_server([job]), job)
    assert score.score >= 90


def test_sudo_command_reduces_score():
    job = _make_job(command="sudo /usr/bin/dangerous")
    score = _score_job(_server([job]), job)
    assert score.score < 100


def test_missing_both_description_and_tags_reduces_score_by_at_least_10():
    job = _make_job(description=None, tags=[])
    score = _score_job(_server([job]), job)
    assert score.score <= 90


def test_multiple_servers_all_scored():
    s1 = Server(name="s1", jobs=[_make_job(name="j1")])
    s2 = Server(name="s2", jobs=[_make_job(name="j2"), _make_job(name="j3")])
    config = Config(servers=[s1, s2])
    result = score_config(config)
    assert len(result.scores) == 3
    assert {s.server_name for s in result.scores} == {"s1", "s2"}


def test_score_summary_includes_grade():
    job = _make_job()
    score = _score_job(_server([job]), job)
    summary = score.summary()
    assert score.grade() in summary
    assert "prod01" in summary
    assert "sync" in summary


def test_config_with_all_bad_jobs_is_not_healthy():
    jobs = [
        _make_job(name=f"j{i}", schedule="not-valid", description=None, tags=[])
        for i in range(3)
    ]
    config = Config(servers=[_server(jobs)])
    result = score_config(config)
    assert result.is_healthy() is False
