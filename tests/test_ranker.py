import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.ranker import rank_config, RankResult, RankedJob


def _make_job(name: str, schedule: str = "0 * * * *", command: str = "/usr/bin/backup.sh",
             description: str = "A job", tags=None) -> CronJob:
    return CronJob(
        name=name,
        schedule=schedule,
        command=command,
        description=description,
        tags=tags or ["ops"],
    )


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def test_rank_config_returns_rank_result():
    job = _make_job("job1")
    server = Server(name="web", jobs=[job])
    result = rank_config(_make_config(server))
    assert isinstance(result, RankResult)


def test_rank_result_total_matches_jobs():
    jobs = [_make_job(f"job{i}") for i in range(4)]
    server = Server(name="web", jobs=jobs)
    result = rank_config(_make_config(server))
    assert result.total() == 4


def test_rank_result_is_empty_false_when_jobs_exist():
    job = _make_job("j")
    server = Server(name="s", jobs=[job])
    result = rank_config(_make_config(server))
    assert not result.is_empty()


def test_rank_result_is_empty_true_when_no_jobs():
    server = Server(name="s", jobs=[])
    result = rank_config(_make_config(server))
    assert result.is_empty()


def test_ranked_job_has_correct_fields():
    job = _make_job("myjob")
    server = Server(name="prod", jobs=[job])
    result = rank_config(_make_config(server))
    entry = result.entries[0]
    assert isinstance(entry, RankedJob)
    assert entry.rank == 1
    assert entry.server == "prod"
    assert entry.job.name == "myjob"
    assert isinstance(entry.score, float)


def test_well_configured_job_scores_higher_than_poor_job():
    good = _make_job("good", description="Does something", tags=["backup"])
    poor = CronJob(name="poor", schedule="* * * * *", command="sudo rm -rf /tmp",
                   description=None, tags=[])
    server = Server(name="s", jobs=[good, poor])
    result = rank_config(_make_config(server), ascending=False)
    assert result.entries[0].job.name == "good"


def test_ascending_order_puts_lowest_score_first():
    good = _make_job("good", description="Solid", tags=["ops"])
    poor = CronJob(name="poor", schedule="* * * * *", command="sudo do_thing",
                   description=None, tags=[])
    server = Server(name="s", jobs=[good, poor])
    result = rank_config(_make_config(server), ascending=True)
    assert result.entries[0].job.name == "poor"


def test_limit_restricts_result_count():
    jobs = [_make_job(f"job{i}") for i in range(10)]
    server = Server(name="s", jobs=jobs)
    result = rank_config(_make_config(server), limit=3)
    assert result.total() == 3


def test_top_returns_correct_slice():
    jobs = [_make_job(f"job{i}") for i in range(8)]
    server = Server(name="s", jobs=jobs)
    result = rank_config(_make_config(server))
    top3 = result.top(3)
    assert len(top3) == 3
    assert all(isinstance(e, RankedJob) for e in top3)


def test_ranked_job_summary_contains_name():
    job = _make_job("backup-db")
    server = Server(name="db", jobs=[job])
    result = rank_config(_make_config(server))
    assert "backup-db" in result.entries[0].summary()


def test_sudo_command_reduces_score():
    normal = _make_job("normal", command="/usr/bin/clean.sh")
    sudo_job = CronJob(name="sudo_job", schedule="0 * * * *",
                       command="sudo /usr/bin/clean.sh", description="Needs root", tags=["ops"])
    server = Server(name="s", jobs=[normal, sudo_job])
    result = rank_config(_make_config(server), ascending=False)
    assert result.entries[0].job.name == "normal"
