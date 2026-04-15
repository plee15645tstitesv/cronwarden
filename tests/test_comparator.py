"""Tests for cronwarden.comparator."""

import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.comparator import compare_configs, ComparisonResult, JobComparison


def _make_job(name="backup", schedule="0 2 * * *", command="/backup.sh", description=None):
    return CronJob(name=name, schedule=schedule, command=command, description=description)


def _make_config(*servers):
    return Config(servers=list(servers))


def test_compare_identical_configs_returns_no_differences():
    job = _make_job()
    server = Server(name="web1", jobs=[job])
    config = _make_config(server)
    result = compare_configs(config, config, "a", "b")
    assert not result.has_differences()
    assert result.total() == 0


def test_compare_detects_schedule_change():
    left = _make_config(Server(name="web1", jobs=[_make_job(schedule="0 2 * * *")]))
    right = _make_config(Server(name="web1", jobs=[_make_job(schedule="0 3 * * *")]))
    result = compare_configs(left, right)
    assert result.has_differences()
    fields = [d.field for d in result.differences]
    assert "schedule" in fields


def test_compare_detects_command_change():
    left = _make_config(Server(name="web1", jobs=[_make_job(command="/old.sh")]))
    right = _make_config(Server(name="web1", jobs=[_make_job(command="/new.sh")]))
    result = compare_configs(left, right)
    assert result.has_differences()
    assert any(d.field == "command" for d in result.differences)


def test_compare_detects_description_change():
    left = _make_config(Server(name="web1", jobs=[_make_job(description="old desc")]))
    right = _make_config(Server(name="web1", jobs=[_make_job(description="new desc")]))
    result = compare_configs(left, right)
    assert any(d.field == "description" for d in result.differences)


def test_compare_detects_added_job():
    left = _make_config(Server(name="web1", jobs=[]))
    right = _make_config(Server(name="web1", jobs=[_make_job()]))
    result = compare_configs(left, right)
    assert result.has_differences()
    assert all(d.left_value is None for d in result.differences)


def test_compare_detects_removed_job():
    left = _make_config(Server(name="web1", jobs=[_make_job()]))
    right = _make_config(Server(name="web1", jobs=[]))
    result = compare_configs(left, right)
    assert result.has_differences()
    assert all(d.right_value is None for d in result.differences)


def test_comparison_result_str_no_differences():
    result = ComparisonResult(left_label="a", right_label="b")
    assert "No differences" in str(result)


def test_comparison_result_str_with_differences():
    result = ComparisonResult(
        left_label="a",
        right_label="b",
        differences=[
            JobComparison(server="web1", job_name="backup", field="schedule",
                          left_value="0 2 * * *", right_value="0 3 * * *")
        ],
    )
    text = str(result)
    assert "1 difference" in text
    assert "backup" in text
    assert "schedule" in text


def test_job_comparison_summary():
    diff = JobComparison(
        server="web1", job_name="backup", field="command",
        left_value="/old.sh", right_value="/new.sh"
    )
    s = diff.summary()
    assert "web1" in s
    assert "backup" in s
    assert "command" in s


def test_labels_preserved_in_result():
    config = _make_config(Server(name="web1", jobs=[]))
    result = compare_configs(config, config, left_label="prod", right_label="staging")
    assert result.left_label == "prod"
    assert result.right_label == "staging"
