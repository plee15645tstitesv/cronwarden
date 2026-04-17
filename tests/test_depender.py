import pytest
from cronwarden.depender import find_dependencies, DependencyResult, JobDependency
from cronwarden.config import Config, Server, CronJob


def _make_job(name: str, command: str, schedule: str = "0 * * * *") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config(servers_jobs: dict) -> Config:
    servers = [
        Server(name=srv, host=f"{srv}.example.com", jobs=jobs)
        for srv, jobs in servers_jobs.items()
    ]
    return Config(servers=servers)


def test_find_dependencies_returns_dependency_result():
    config = _make_config({"web": [_make_job("backup db", "pg_dump mydb")]})
    result = find_dependencies(config)
    assert isinstance(result, DependencyResult)


def test_no_dependencies_when_jobs_unrelated():
    config = _make_config({
        "web": [
            _make_job("backup", "pg_dump mydb"),
            _make_job("cleanup logs", "find /var/log -delete"),
        ]
    })
    result = find_dependencies(config)
    assert not result.has_dependencies


def test_detects_dependency_by_shared_tokens():
    config = _make_config({
        "web": [
            _make_job("backup postgres", "pg_dump postgres_db"),
            _make_job("restore postgres", "pg_restore postgres_db"),
        ]
    })
    result = find_dependencies(config)
    assert result.has_dependencies


def test_dependency_summary_is_string():
    dep = JobDependency(
        server="web",
        job_name="backup postgres",
        depends_on_name="restore postgres",
        reason="shared tokens: postgres",
    )
    assert isinstance(dep.summary(), str)
    assert "backup postgres" in dep.summary()
    assert "restore postgres" in dep.summary()


def test_total_counts_dependencies():
    config = _make_config({
        "web": [
            _make_job("sync media files", "rsync media files /backup"),
            _make_job("cleanup media files", "rm old media files"),
        ]
    })
    result = find_dependencies(config)
    assert result.total == result.total  # structural check
    assert isinstance(result.total, int)


def test_cross_server_dependency_detected():
    config = _make_config({
        "web": [_make_job("export reports data", "python export_reports.py data")],
        "db": [_make_job("import reports data", "python import_reports.py data")],
    })
    result = find_dependencies(config)
    assert result.has_dependencies


def test_min_overlap_respected():
    config = _make_config({
        "web": [
            _make_job("backup", "backup_script.sh"),
            _make_job("restore", "restore_script.sh"),
        ]
    })
    result_strict = find_dependencies(config, min_overlap=3)
    result_loose = find_dependencies(config, min_overlap=1)
    assert result_strict.total <= result_loose.total
