import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.pauser import pause_jobs, PauseResult, PausedJob


def _make_job(name: str, schedule: str = "0 * * * *", command: str = "echo hi") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config() -> Config:
    return Config(
        servers=[
            Server(
                name="web-01",
                jobs=[
                    _make_job("backup", "0 2 * * *", "/usr/bin/backup.sh"),
                    _make_job("cleanup", "0 3 * * *", "/usr/bin/cleanup.sh"),
                ],
            ),
            Server(
                name="db-01",
                jobs=[
                    _make_job("backup", "0 2 * * *", "/usr/bin/db-backup.sh"),
                    _make_job("report", "0 6 * * 1", "/usr/bin/report.sh"),
                ],
            ),
        ]
    )


def test_pause_jobs_returns_pause_result():
    config = _make_config()
    result = pause_jobs(config, ["backup"])
    assert isinstance(result, PauseResult)


def test_pause_jobs_matches_across_servers():
    config = _make_config()
    result = pause_jobs(config, ["backup"])
    assert result.total == 2
    servers = {p.server for p in result.paused}
    assert "web-01" in servers
    assert "db-01" in servers


def test_pause_jobs_has_paused_true_when_matched():
    config = _make_config()
    result = pause_jobs(config, ["cleanup"])
    assert result.has_paused is True


def test_pause_jobs_has_paused_false_when_no_match():
    config = _make_config()
    result = pause_jobs(config, ["nonexistent"])
    assert result.has_paused is False


def test_pause_jobs_skips_unmatched_names():
    config = _make_config()
    result = pause_jobs(config, ["backup", "ghost"])
    assert "ghost" in result.skipped
    assert "backup" not in result.skipped


def test_pause_jobs_stores_reason():
    config = _make_config()
    result = pause_jobs(config, ["report"], reason="maintenance window")
    assert result.total == 1
    assert result.paused[0].reason == "maintenance window"


def test_paused_job_summary_with_reason():
    job = PausedJob(server="web-01", job_name="backup", schedule="0 2 * * *", command="backup.sh", reason="testing")
    assert "web-01" in job.summary()
    assert "backup" in job.summary()
    assert "testing" in job.summary()


def test_paused_job_summary_without_reason():
    job = PausedJob(server="web-01", job_name="backup", schedule="0 2 * * *", command="backup.sh")
    assert "(" not in job.summary()


def test_pause_jobs_empty_name_list():
    config = _make_config()
    result = pause_jobs(config, [])
    assert result.total == 0
    assert result.has_paused is False
