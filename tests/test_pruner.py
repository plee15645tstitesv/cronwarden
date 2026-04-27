"""Tests for cronwarden.pruner."""

import pytest
from cronwarden.pruner import prune_config, PrunedJob, PruneResult
from cronwarden.config import Config, Server, CronJob


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup.sh", **kwargs):
    return CronJob(name=name, schedule=schedule, command=command, **kwargs)


def _make_config(*servers):
    return Config(servers=list(servers))


def _make_server(name="web-01", jobs=None):
    return Server(name=name, jobs=jobs or [])


def test_prune_config_returns_prune_result():
    config = _make_config(_make_server(jobs=[_make_job()]))
    result = prune_config(config)
    assert isinstance(result, PruneResult)


def test_clean_jobs_not_pruned():
    config = _make_config(_make_server(jobs=[_make_job(name="backup", command="/usr/bin/backup.sh")]))
    result = prune_config(config)
    assert not result.has_pruned()


def test_noop_command_is_pruned():
    config = _make_config(_make_server(jobs=[_make_job(name="noop", command="/bin/true")]))
    result = prune_config(config)
    assert result.has_pruned()
    assert result.pruned[0].reason == "command is a no-op"


def test_true_command_is_pruned():
    config = _make_config(_make_server(jobs=[_make_job(name="noop2", command="true")]))
    result = prune_config(config)
    assert result.has_pruned()


def test_disabled_prefix_is_pruned():
    config = _make_config(_make_server(jobs=[_make_job(name="disabled_cleanup", command="/bin/cleanup.sh")]))
    result = prune_config(config)
    assert result.has_pruned()
    assert "disabled" in result.pruned[0].reason


def test_old_prefix_is_pruned():
    config = _make_config(_make_server(jobs=[_make_job(name="old_sync", command="/bin/sync.sh")]))
    result = prune_config(config)
    assert result.has_pruned()


def test_never_run_list_flags_job():
    config = _make_config(_make_server(jobs=[_make_job(name="rarely_run", command="/opt/run.sh")]))
    result = prune_config(config, never_run_names=["rarely_run"])
    assert result.has_pruned()
    assert "never executed" in result.pruned[0].reason


def test_never_run_list_ignores_other_jobs():
    job1 = _make_job(name="job_a", command="/bin/a.sh")
    job2 = _make_job(name="job_b", command="/bin/b.sh")
    config = _make_config(_make_server(jobs=[job1, job2]))
    result = prune_config(config, never_run_names=["job_a"])
    assert result.total() == 1
    assert result.pruned[0].job_name == "job_a"


def test_total_scanned_counts_all_jobs():
    jobs = [_make_job(name=f"job_{i}", command=f"/bin/job{i}.sh") for i in range(5)]
    config = _make_config(_make_server(jobs=jobs))
    result = prune_config(config)
    assert result.total_scanned == 5


def test_prune_result_str_no_pruned():
    result = PruneResult(pruned=[], total_scanned=3)
    assert "No jobs" in str(result)


def test_prune_result_str_with_pruned():
    p = PrunedJob(server="s1", job_name="old_job", schedule="* * * * *", command="true", reason="no-op")
    result = PruneResult(pruned=[p], total_scanned=1)
    assert "old_job" in str(result)


def test_pruned_job_summary():
    p = PrunedJob(server="web", job_name="cleanup", schedule="0 1 * * *", command=":", reason="no-op")
    assert "web" in p.summary()
    assert "cleanup" in p.summary()


def test_multi_server_pruning():
    s1 = _make_server(name="s1", jobs=[_make_job(name="disabled_x", command="/bin/x.sh")])
    s2 = _make_server(name="s2", jobs=[_make_job(name="healthy", command="/bin/healthy.sh")])
    config = _make_config(s1, s2)
    result = prune_config(config)
    assert result.total() == 1
    assert result.pruned[0].server == "s1"
