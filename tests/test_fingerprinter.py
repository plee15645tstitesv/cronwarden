"""Tests for cronwarden.fingerprinter."""

import pytest
from cronwarden.config import Config, CronJob, Server
from cronwarden.fingerprinter import (
    FingerprintEntry,
    FingerprintResult,
    fingerprint_config,
    _job_fingerprint,
)


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup.sh", tags=None):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [])


def _make_config(*server_defs):
    servers = [
        Server(name=sname, host=f"{sname}.example.com", jobs=list(jobs))
        for sname, jobs in server_defs
    ]
    return Config(servers=servers)


def test_fingerprint_config_returns_fingerprint_result():
    config = _make_config(("web", [_make_job()]))
    result = fingerprint_config(config)
    assert isinstance(result, FingerprintResult)


def test_fingerprint_result_total_matches_all_jobs():
    config = _make_config(
        ("web", [_make_job("a"), _make_job("b")]),
        ("db", [_make_job("c")]),
    )
    result = fingerprint_config(config)
    assert result.total == 3


def test_fingerprint_result_is_empty_false_when_jobs_exist():
    config = _make_config(("web", [_make_job()]))
    result = fingerprint_config(config)
    assert result.is_empty is False


def test_fingerprint_result_is_empty_true_when_no_jobs():
    config = _make_config(("web", []))
    result = fingerprint_config(config)
    assert result.is_empty is True


def test_fingerprint_entries_are_fingerprint_entry_instances():
    config = _make_config(("web", [_make_job()]))
    result = fingerprint_config(config)
    assert all(isinstance(e, FingerprintEntry) for e in result.entries)


def test_fingerprint_entry_has_correct_server_and_job():
    job = _make_job(name="cleanup", schedule="0 3 * * *", command="/bin/clean")
    config = _make_config(("prod", [job]))
    result = fingerprint_config(config)
    entry = result.entries[0]
    assert entry.server == "prod"
    assert entry.job_name == "cleanup"
    assert entry.schedule == "0 3 * * *"
    assert entry.command == "/bin/clean"


def test_fingerprint_is_16_hex_chars():
    job = _make_job()
    fp = _job_fingerprint("web", job)
    assert len(fp) == 16
    assert all(c in "0123456789abcdef" for c in fp)


def test_same_job_produces_same_fingerprint():
    job = _make_job()
    fp1 = _job_fingerprint("web", job)
    fp2 = _job_fingerprint("web", job)
    assert fp1 == fp2


def test_different_schedule_produces_different_fingerprint():
    job1 = _make_job(schedule="0 2 * * *")
    job2 = _make_job(schedule="0 3 * * *")
    assert _job_fingerprint("web", job1) != _job_fingerprint("web", job2)


def test_different_server_produces_different_fingerprint():
    job = _make_job()
    assert _job_fingerprint("web", job) != _job_fingerprint("db", job)


def test_get_fingerprint_returns_correct_value():
    job = _make_job(name="sync")
    config = _make_config(("app", [job]))
    result = fingerprint_config(config)
    fp = result.get_fingerprint("app", "sync")
    assert fp is not None
    assert len(fp) == 16


def test_get_fingerprint_returns_none_for_missing():
    config = _make_config(("app", [_make_job()]))
    result = fingerprint_config(config)
    assert result.get_fingerprint("unknown", "nope") is None


def test_as_dict_keys_are_fingerprints():
    config = _make_config(("web", [_make_job("a"), _make_job("b")]))
    result = fingerprint_config(config)
    d = result.as_dict()
    assert len(d) == 2
    for fp, meta in d.items():
        assert "server" in meta
        assert "job" in meta


def test_entry_summary_contains_server_and_fingerprint():
    job = _make_job(name="report")
    config = _make_config(("analytics", [job]))
    result = fingerprint_config(config)
    s = result.entries[0].summary()
    assert "analytics" in s
    assert "report" in s
