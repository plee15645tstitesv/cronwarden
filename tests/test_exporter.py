"""Tests for cronwarden.exporter."""
from __future__ import annotations

import csv
import io
from pathlib import Path

import pytest

from cronwarden.config import Config, Server, CronJob
from cronwarden.exporter import export_csv, export_table


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup",
              tags=None, description=None, user=None):
    return CronJob(
        name=name,
        schedule=schedule,
        command=command,
        tags=tags or [],
        description=description,
        user=user,
    )


def _make_config(jobs=None, server_name="web-01"):
    jobs = jobs or [_make_job()]
    server = Server(name=server_name, jobs=jobs)
    return Config(servers=[server])


# --- export_csv ---

def test_export_csv_returns_string():
    config = _make_config()
    result = export_csv(config)
    assert isinstance(result, str)


def test_export_csv_has_header_row():
    config = _make_config()
    result = export_csv(config)
    reader = csv.reader(io.StringIO(result))
    header = next(reader)
    assert "server" in header
    assert "job_name" in header
    assert "schedule" in header
    assert "valid" in header


def test_export_csv_contains_server_name():
    config = _make_config(server_name="prod-01")
    result = export_csv(config)
    assert "prod-01" in result


def test_export_csv_contains_job_fields():
    job = _make_job(name="cleanup", schedule="@daily", command="/bin/clean",
                    tags=["ops"], description="Cleanup job", user="root")
    config = _make_config(jobs=[job])
    result = export_csv(config)
    assert "cleanup" in result
    assert "@daily" in result
    assert "/bin/clean" in result
    assert "ops" in result
    assert "root" in result


def test_export_csv_valid_flag_for_valid_job():
    config = _make_config(jobs=[_make_job(schedule="0 * * * *")])
    result = export_csv(config)
    assert ",yes" in result or "yes," in result or result.count("yes") >= 1


def test_export_csv_valid_flag_for_invalid_job():
    config = _make_config(jobs=[_make_job(schedule="not-a-cron")])
    result = export_csv(config)
    assert "no" in result


# --- export_table ---

def test_export_table_returns_string():
    config = _make_config()
    result = export_table(config)
    assert isinstance(result, str)


def test_export_table_contains_header():
    config = _make_config()
    result = export_table(config)
    assert "SERVER" in result
    assert "JOB" in result
    assert "SCHEDULE" in result


def test_export_table_contains_job_name():
    job = _make_job(name="nightly-sync")
    config = _make_config(jobs=[job])
    result = export_table(config)
    assert "nightly-sync" in result


def test_export_table_no_jobs_message():
    server = Server(name="empty-server", jobs=[])
    config = Config(servers=[server])
    result = export_table(config)
    assert "No jobs found." in result


def test_export_table_truncates_long_commands():
    long_cmd = "/usr/bin/" + "a" * 60
    job = _make_job(command=long_cmd)
    config = _make_config(jobs=[job])
    result = export_table(config)
    assert "..." in result
