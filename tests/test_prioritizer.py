import pytest
from cronwarden.prioritizer import prioritize_config, PriorityResult, PrioritizedJob, _detect_priority
from cronwarden.config import Config, Server, CronJob


def _make_job(name="job", command="run.sh", schedule="0 * * * *", tags=None):
    return CronJob(name=name, command=command, schedule=schedule, tags=tags or [])


def _make_config(*servers):
    return Config(servers=list(servers))


def _make_server(name="web", jobs=None):
    return Server(name=name, host="localhost", jobs=jobs or [])


def test_prioritize_returns_priority_result():
    config = _make_config(_make_server(jobs=[_make_job()]))
    result = prioritize_config(config)
    assert isinstance(result, PriorityResult)


def test_backup_job_is_critical():
    job = _make_job(name="backup-db", command="/usr/bin/backup.sh")
    priority, reason = _detect_priority(job)
    assert priority == "critical"
    assert "backup" in reason


def test_payment_command_is_critical():
    job = _make_job(name="run", command="process_payment.py")
    priority, _ = _detect_priority(job)
    assert priority == "critical"


def test_sync_job_is_high():
    job = _make_job(name="sync-users", command="sync.sh")
    priority, _ = _detect_priority(job)
    assert priority == "high"


def test_unknown_job_is_normal():
    job = _make_job(name="myjob", command="/opt/run.sh")
    priority, reason = _detect_priority(job)
    assert priority == "normal"
    assert "no priority" in reason


def test_total_counts_all_jobs():
    server = _make_server(jobs=[_make_job("a"), _make_job("b"), _make_job("c")])
    result = prioritize_config(_make_config(server))
    assert result.total() == 3


def test_has_critical_true_when_backup_present():
    server = _make_server(jobs=[_make_job(name="backup-logs", command="backup.sh")])
    result = prioritize_config(_make_config(server))
    assert result.has_critical() is True


def test_has_critical_false_when_no_critical():
    server = _make_server(jobs=[_make_job(name="ping", command="ping.sh")])
    result = prioritize_config(_make_config(server))
    assert result.has_critical() is False


def test_by_priority_filters_correctly():
    jobs = [
        _make_job(name="backup", command="backup.sh"),
        _make_job(name="ping", command="ping.sh"),
    ]
    server = _make_server(jobs=jobs)
    result = prioritize_config(_make_config(server))
    critical = result.by_priority("critical")
    assert len(critical) == 1
    assert critical[0].job.name == "backup"


def test_entry_summary_contains_server_and_job():
    job = _make_job(name="backup-data", command="backup.sh")
    server = _make_server(name="prod", jobs=[job])
    result = prioritize_config(_make_config(server))
    summary = result.entries[0].summary()
    assert "prod" in summary
    assert "backup-data" in summary
