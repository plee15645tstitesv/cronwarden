import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.cloner import clone_jobs, CloneResult, ClonedJob


def _make_job(name, schedule="0 * * * *", command="echo hi", tags=None):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [])


def _make_config():
    src = Server(name="src", host="1.2.3.4", jobs=[
        _make_job("backup", schedule="0 2 * * *", command="/usr/bin/backup"),
        _make_job("cleanup", schedule="0 3 * * *", command="/usr/bin/cleanup"),
    ])
    dst = Server(name="dst", host="5.6.7.8", jobs=[
        _make_job("existing", schedule="0 4 * * *", command="/usr/bin/existing"),
    ])
    return Config(servers=[src, dst])


def test_clone_jobs_returns_clone_result():
    config = _make_config()
    result = clone_jobs(config, ["backup"], "src", "dst")
    assert isinstance(result, CloneResult)


def test_clone_single_job():
    config = _make_config()
    result = clone_jobs(config, ["backup"], "src", "dst")
    assert result.total == 1
    assert result.has_clones


def test_cloned_job_fields():
    config = _make_config()
    result = clone_jobs(config, ["backup"], "src", "dst")
    c = result.cloned[0]
    assert isinstance(c, ClonedJob)
    assert c.job_name == "backup"
    assert c.source_server == "src"
    assert c.target_server == "dst"
    assert c.schedule == "0 2 * * *"
    assert c.command == "/usr/bin/backup"


def test_clone_multiple_jobs():
    config = _make_config()
    result = clone_jobs(config, ["backup", "cleanup"], "src", "dst")
    assert result.total == 2


def test_clone_skips_existing_job():
    config = _make_config()
    result = clone_jobs(config, ["existing"], "src", "dst")
    # 'existing' is not on src, so not cloned
    assert result.total == 0


def test_clone_skips_duplicate_on_target():
    config = _make_config()
    # Add backup to dst first
    config.servers[1].jobs.append(_make_job("backup"))
    result = clone_jobs(config, ["backup"], "src", "dst")
    assert result.total == 0
    assert "backup" in result.skipped


def test_clone_invalid_source_returns_empty():
    config = _make_config()
    result = clone_jobs(config, ["backup"], "nonexistent", "dst")
    assert not result.has_clones


def test_clone_invalid_target_returns_empty():
    config = _make_config()
    result = clone_jobs(config, ["backup"], "src", "nonexistent")
    assert not result.has_clones


def test_cloned_job_summary():
    c = ClonedJob(source_server="src", target_server="dst", job_name="backup",
                  schedule="0 2 * * *", command="/usr/bin/backup")
    assert "backup" in c.summary()
    assert "src" in c.summary()
    assert "dst" in c.summary()


def test_clone_appends_to_target_server():
    config = _make_config()
    before = len(config.servers[1].jobs)
    clone_jobs(config, ["backup"], "src", "dst")
    assert len(config.servers[1].jobs) == before + 1
