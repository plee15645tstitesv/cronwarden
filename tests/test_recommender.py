import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.recommender import recommend, Recommendation, RecommendationResult


def _make_job(
    name="backup",
    schedule="0 2 * * *",
    command="/usr/bin/backup.sh",
    description="Nightly backup",
    tags=None,
):
    return CronJob(
        name=name,
        schedule=schedule,
        command=command,
        description=description,
        tags=tags or ["backup"],
    )


def _make_config(jobs=None, server_name="web-01"):
    server = Server(name=server_name, jobs=jobs or [_make_job()])
    return Config(servers=[server])


def test_recommend_returns_recommendation_result():
    config = _make_config()
    result = recommend(config)
    assert isinstance(result, RecommendationResult)


def test_clean_job_has_no_recommendations():
    config = _make_config()
    result = recommend(config)
    assert not result.has_recommendations
    assert result.total == 0


def test_r001_every_minute_schedule():
    job = _make_job(schedule="* * * * *")
    config = _make_config(jobs=[job])
    result = recommend(config)
    codes = [r.code for r in result.recommendations]
    assert "R001" in codes


def test_r002_sudo_command():
    job = _make_job(command="sudo /usr/bin/cleanup.sh")
    config = _make_config(jobs=[job])
    result = recommend(config)
    codes = [r.code for r in result.recommendations]
    assert "R002" in codes


def test_r003_no_tags():
    job = _make_job(tags=[])
    config = _make_config(jobs=[job])
    result = recommend(config)
    codes = [r.code for r in result.recommendations]
    assert "R003" in codes


def test_r004_no_description():
    job = _make_job(description=None)
    config = _make_config(jobs=[job])
    result = recommend(config)
    codes = [r.code for r in result.recommendations]
    assert "R004" in codes


def test_multiple_issues_on_same_job():
    job = _make_job(schedule="* * * * *", description=None, tags=[])
    config = _make_config(jobs=[job])
    result = recommend(config)
    assert result.total >= 3


def test_recommendation_summary_contains_code():
    job = _make_job(tags=[])
    config = _make_config(jobs=[job])
    result = recommend(config)
    rec = next(r for r in result.recommendations if r.code == "R003")
    assert "R003" in rec.summary()
    assert rec.server in rec.summary()
    assert rec.job_name in rec.summary()


def test_recommendations_span_multiple_servers():
    s1 = Server(name="s1", jobs=[_make_job(tags=[])])
    s2 = Server(name="s2", jobs=[_make_job(tags=[])])
    config = Config(servers=[s1, s2])
    result = recommend(config)
    servers = {r.server for r in result.recommendations}
    assert "s1" in servers
    assert "s2" in servers


def test_has_recommendations_true_when_issues_exist():
    job = _make_job(description=None)
    config = _make_config(jobs=[job])
    result = recommend(config)
    assert result.has_recommendations is True
