import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.renamer import rename_job, RenameResult, RenameChange


def _make_job(name: str, schedule: str = "0 * * * *", command: str = "echo hi") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config() -> Config:
    return Config(servers=[
        Server(name="web", host="web.example.com", jobs=[
            _make_job("backup"),
            _make_job("cleanup"),
        ]),
        Server(name="db", host="db.example.com", jobs=[
            _make_job("backup"),
            _make_job("report"),
        ]),
    ])


def test_rename_job_returns_rename_result():
    config = _make_config()
    result = rename_job(config, "backup", "backup-v2")
    assert isinstance(result, RenameResult)


def test_rename_job_detects_changes():
    config = _make_config()
    result = rename_job(config, "backup", "backup-v2")
    assert result.has_changes


def test_rename_job_counts_all_servers():
    config = _make_config()
    result = rename_job(config, "backup", "backup-v2")
    assert result.total == 2


def test_rename_job_updates_name_in_config():
    config = _make_config()
    rename_job(config, "cleanup", "cleanup-v2")
    names = [j.name for s in config.servers for j in s.jobs]
    assert "cleanup-v2" in names
    assert "cleanup" not in names


def test_rename_job_change_summary_format():
    config = _make_config()
    result = rename_job(config, "report", "daily-report")
    assert result.total == 1
    assert result.changes[0].summary() == "[db] 'report' -> 'daily-report'"


def test_rename_job_not_found():
    config = _make_config()
    result = rename_job(config, "nonexistent", "something")
    assert not result.has_changes
    assert "nonexistent" in result.not_found


def test_rename_job_raises_on_empty_old_name():
    config = _make_config()
    with pytest.raises(ValueError):
        rename_job(config, "", "new-name")


def test_rename_job_raises_on_empty_new_name():
    config = _make_config()
    with pytest.raises(ValueError):
        rename_job(config, "backup", "")


def test_rename_job_does_not_affect_other_jobs():
    config = _make_config()
    rename_job(config, "backup", "backup-v2")
    names = [j.name for s in config.servers for j in s.jobs]
    assert "cleanup" in names
    assert "report" in names
