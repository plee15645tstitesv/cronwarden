"""Tests for cronwarden.differ module."""

import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.differ import diff_configs, DiffResult, JobDiff


def _make_config(servers_data: list) -> Config:
    servers = []
    for s in servers_data:
        jobs = [CronJob(name=j["name"], schedule=j["schedule"], command=j["command"],
                        description=j.get("description")) for j in s["jobs"]]
        servers.append(Server(name=s["name"], host=s.get("host", "localhost"), jobs=jobs))
    return Config(servers=servers)


def test_no_changes_returns_empty_diff():
    cfg = _make_config([{"name": "web", "jobs": [{"name": "backup", "schedule": "0 2 * * *", "command": "/backup.sh"}]}])
    result = diff_configs(cfg, cfg)
    assert not result.has_changes
    assert result.diffs == []


def test_added_job_detected():
    old = _make_config([{"name": "web", "jobs": []}])
    new = _make_config([{"name": "web", "jobs": [{"name": "cleanup", "schedule": "@daily", "command": "/clean.sh"}]}])
    result = diff_configs(old, new)
    assert result.has_changes
    assert len(result.added()) == 1
    assert result.added()[0].job_name == "cleanup"
    assert result.added()[0].kind == "added"


def test_removed_job_detected():
    old = _make_config([{"name": "web", "jobs": [{"name": "cleanup", "schedule": "@daily", "command": "/clean.sh"}]}])
    new = _make_config([{"name": "web", "jobs": []}])
    result = diff_configs(old, new)
    assert len(result.removed()) == 1
    assert result.removed()[0].kind == "removed"
    assert result.removed()[0].job_name == "cleanup"


def test_changed_schedule_detected():
    old = _make_config([{"name": "web", "jobs": [{"name": "report", "schedule": "0 8 * * *", "command": "/report.sh"}]}])
    new = _make_config([{"name": "web", "jobs": [{"name": "report", "schedule": "0 9 * * *", "command": "/report.sh"}]}])
    result = diff_configs(old, new)
    assert len(result.changed()) == 1
    diff = result.changed()[0]
    assert diff.old_value["schedule"] == "0 8 * * *"
    assert diff.new_value["schedule"] == "0 9 * * *"


def test_changed_command_detected():
    old = _make_config([{"name": "db", "jobs": [{"name": "dump", "schedule": "@daily", "command": "/dump_v1.sh"}]}])
    new = _make_config([{"name": "db", "jobs": [{"name": "dump", "schedule": "@daily", "command": "/dump_v2.sh"}]}])
    result = diff_configs(old, new)
    assert len(result.changed()) == 1


def test_job_diff_summary_added():
    d = JobDiff(server="web", job_name="task", kind="added", new_value={"schedule": "@daily", "command": "/t.sh", "description": None})
    assert "[+]" in d.summary()
    assert "web/task" in d.summary()


def test_job_diff_summary_removed():
    d = JobDiff(server="web", job_name="task", kind="removed", old_value={"schedule": "@daily", "command": "/t.sh", "description": None})
    assert "[-]" in d.summary()


def test_job_diff_summary_changed():
    d = JobDiff(server="web", job_name="task", kind="changed",
                old_value={"schedule": "0 8 * * *", "command": "/t.sh", "description": None},
                new_value={"schedule": "0 9 * * *", "command": "/t.sh", "description": None})
    summary = d.summary()
    assert "[~]" in summary
    assert "schedule" in summary


def test_multiple_servers_diffed_independently():
    old = _make_config([
        {"name": "web", "jobs": [{"name": "job1", "schedule": "@hourly", "command": "/a.sh"}]},
        {"name": "db", "jobs": [{"name": "job2", "schedule": "@daily", "command": "/b.sh"}]},
    ])
    new = _make_config([
        {"name": "web", "jobs": []},
        {"name": "db", "jobs": [{"name": "job2", "schedule": "@daily", "command": "/b.sh"}]},
    ])
    result = diff_configs(old, new)
    assert len(result.removed()) == 1
    assert result.removed()[0].server == "web"
    assert len(result.changed()) == 0
