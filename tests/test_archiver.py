import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.archiver import (
    archive_jobs,
    restore_jobs,
    ArchiveResult,
    ARCHIVE_MARKER,
)


def _make_job(name: str, command: str = "/usr/bin/backup.sh") -> CronJob:
    return CronJob(name=name, schedule="0 2 * * *", command=command)


def _make_config(*job_pairs) -> Config:
    """job_pairs: list of (server_name, [jobs])"""
    servers = [
        Server(name=sname, host=f"{sname}.example.com", jobs=jobs)
        for sname, jobs in job_pairs
    ]
    return Config(servers=servers)


def test_archive_jobs_returns_archive_result():
    config = _make_config(("web", [_make_job("backup")]))
    result = archive_jobs(config, ["backup"])
    assert isinstance(result, ArchiveResult)


def test_archive_job_marks_command():
    config = _make_config(("web", [_make_job("backup", "/usr/bin/backup.sh")]))
    result = archive_jobs(config, ["backup"])
    assert len(result.archived) == 1
    assert result.archived[0].archived_command.startswith(ARCHIVE_MARKER)


def test_archive_mutates_job_command():
    job = _make_job("backup", "/usr/bin/backup.sh")
    config = _make_config(("web", [job]))
    archive_jobs(config, ["backup"])
    assert job.command.startswith(ARCHIVE_MARKER)


def test_archive_already_archived_job_is_skipped():
    cmd = f"{ARCHIVE_MARKER} /usr/bin/backup.sh"
    config = _make_config(("web", [_make_job("backup", cmd)]))
    result = archive_jobs(config, ["backup"])
    assert len(result.archived) == 0
    assert len(result.skipped) == 1


def test_archive_filters_by_server_name():
    config = _make_config(
        ("web", [_make_job("backup")]),
        ("db", [_make_job("backup")]),
    )
    result = archive_jobs(config, ["backup"], server_name="web")
    assert len(result.archived) == 1
    assert result.archived[0].server_name == "web"


def test_restore_job_removes_marker():
    cmd = f"{ARCHIVE_MARKER} /usr/bin/backup.sh"
    job = _make_job("backup", cmd)
    config = _make_config(("web", [job]))
    result = restore_jobs(config, ["backup"])
    assert len(result.restored) == 1
    assert not job.command.startswith(ARCHIVE_MARKER)
    assert job.command == "/usr/bin/backup.sh"


def test_restore_non_archived_job_is_skipped():
    config = _make_config(("web", [_make_job("backup")]))
    result = restore_jobs(config, ["backup"])
    assert len(result.restored) == 0
    assert len(result.skipped) == 1


def test_archive_result_has_changes_true_when_archived():
    config = _make_config(("web", [_make_job("backup")]))
    result = archive_jobs(config, ["backup"])
    assert result.has_changes is True


def test_archive_result_has_changes_false_when_only_skipped():
    cmd = f"{ARCHIVE_MARKER} /usr/bin/backup.sh"
    config = _make_config(("web", [_make_job("backup", cmd)]))
    result = archive_jobs(config, ["backup"])
    assert result.has_changes is False


def test_archive_result_summary_on_archived_job():
    config = _make_config(("web", [_make_job("backup")]))
    result = archive_jobs(config, ["backup"])
    assert result.archived[0].summary == "[web] backup: archived"


def test_archive_unmatched_job_name_produces_no_changes():
    config = _make_config(("web", [_make_job("backup")]))
    result = archive_jobs(config, ["nonexistent"])
    assert not result.has_changes
    assert result.total_archived == 0
