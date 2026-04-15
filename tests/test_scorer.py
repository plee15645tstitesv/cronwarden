"""Tests for cronwarden.scorer."""
import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.scorer import JobScore, ScoreResult, score_config, _score_job


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup",
              description="Nightly backup", tags=None):
    return CronJob(
        name=name,
        schedule=schedule,
        command=command,
        description=description,
        tags=tags or ["backup"],
    )


def _make_config(jobs=None):
    if jobs is None:
        jobs = [_make_job()]
    server = Server(name="web01", jobs=jobs)
    return Config(servers=[server])


def test_score_config_returns_score_result():
    config = _make_config()
    result = score_config(config)
    assert isinstance(result, ScoreResult)


def test_perfect_job_scores_high():
    job = _make_job()
    server = Server(name="web01", jobs=[job])
    score = _score_job(server, job)
    assert score.score >= 90


def test_job_without_description_loses_points():
    job = _make_job(description=None)
    server = Server(name="web01", jobs=[job])
    score = _score_job(server, job)
    assert score.score < 100
    assert any("description" in r for r in score.reasons)


def test_job_without_tags_loses_points():
    job = _make_job(tags=[])
    server = Server(name="web01", jobs=[job])
    score = _score_job(server, job)
    assert score.score < 100
    assert any("tags" in r for r in score.reasons)


def test_invalid_schedule_loses_points():
    job = _make_job(schedule="not-a-cron")
    server = Server(name="web01", jobs=[job])
    score = _score_job(server, job)
    assert score.score <= 60


def test_grade_a_for_high_score():
    s = JobScore(server_name="s", job_name="j", score=95)
    assert s.grade() == "A"


def test_grade_f_for_low_score():
    s = JobScore(server_name="s", job_name="j", score=30)
    assert s.grade() == "F"


def test_score_result_average():
    scores = [
        JobScore(server_name="s", job_name="j1", score=80),
        JobScore(server_name="s", job_name="j2", score=60),
    ]
    result = ScoreResult(scores=scores)
    assert result.average_score() == 70.0


def test_score_result_empty_average():
    result = ScoreResult(scores=[])
    assert result.average_score() == 0.0


def test_score_result_lowest_and_highest():
    scores = [
        JobScore(server_name="s", job_name="j1", score=80),
        JobScore(server_name="s", job_name="j2", score=40),
    ]
    result = ScoreResult(scores=scores)
    assert result.lowest().score == 40
    assert result.highest().score == 80


def test_is_healthy_true_when_average_high():
    scores = [JobScore(server_name="s", job_name=f"j{i}", score=90) for i in range(3)]
    result = ScoreResult(scores=scores)
    assert result.is_healthy() is True


def test_is_healthy_false_when_average_low():
    scores = [JobScore(server_name="s", job_name=f"j{i}", score=40) for i in range(3)]
    result = ScoreResult(scores=scores)
    assert result.is_healthy() is False


def test_score_config_counts_all_jobs():
    jobs = [_make_job(name=f"job{i}") for i in range(4)]
    config = _make_config(jobs=jobs)
    result = score_config(config)
    assert len(result.scores) == 4
