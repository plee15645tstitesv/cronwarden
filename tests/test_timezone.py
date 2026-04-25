"""Tests for cronwarden.timezone module."""

import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.timezone import (
    TimezoneAnnotation,
    TimezoneResult,
    annotate_timezones,
)


def _make_job(name="backup", schedule="0 2 * * *", tags=None):
    return CronJob(
        name=name,
        schedule=schedule,
        command=f"/usr/bin/{name}.sh",
        description=None,
        tags=tags or [],
    )


def _make_config(*servers):
    return Config(servers=list(servers))


def _make_server(name="web-01", jobs=None, timezone=None):
    server = Server(name=name, jobs=jobs or [])
    if timezone:
        server.timezone = timezone
    return server


# --- TimezoneResult tests ---

def test_timezone_result_empty_has_no_missing():
    result = TimezoneResult()
    assert not result.has_missing


def test_timezone_result_total_zero_when_empty():
    result = TimezoneResult()
    assert result.total == 0


def test_timezone_result_has_missing_true_when_annotation_lacks_tz():
    ann = TimezoneAnnotation(
        server="s1", job_name="j1", command="cmd",
        schedule="* * * * *", timezone=None, inferred=False
    )
    result = TimezoneResult(annotations=[ann])
    assert result.has_missing


def test_timezone_result_missing_count():
    a1 = TimezoneAnnotation("s", "j1", "c", "* * * * *", timezone=None, inferred=False)
    a2 = TimezoneAnnotation("s", "j2", "c", "* * * * *", timezone="UTC", inferred=True)
    result = TimezoneResult(annotations=[a1, a2])
    assert result.missing_count == 1


def test_jobs_without_timezone_filters_correctly():
    a1 = TimezoneAnnotation("s", "j1", "c", "* * * * *", timezone=None, inferred=False)
    a2 = TimezoneAnnotation("s", "j2", "c", "* * * * *", timezone="UTC", inferred=False)
    result = TimezoneResult(annotations=[a1, a2])
    missing = result.jobs_without_timezone()
    assert len(missing) == 1
    assert missing[0].job_name == "j1"


# --- annotate_timezones tests ---

def test_annotate_returns_timezone_result():
    config = _make_config(_make_server(jobs=[_make_job()]))
    result = annotate_timezones(config)
    assert isinstance(result, TimezoneResult)


def test_no_tz_info_results_in_missing():
    config = _make_config(_make_server(jobs=[_make_job()]))
    result = annotate_timezones(config)
    assert result.has_missing


def test_default_tz_propagates_to_all_jobs():
    jobs = [_make_job("j1"), _make_job("j2")]
    config = _make_config(_make_server(jobs=jobs))
    result = annotate_timezones(config, default_tz="America/New_York")
    assert all(a.timezone == "America/New_York" for a in result.annotations)
    assert all(a.inferred for a in result.annotations)


def test_tz_tag_overrides_default():
    job = _make_job(tags=["tz:Europe/London"])
    config = _make_config(_make_server(jobs=[job]))
    result = annotate_timezones(config, default_tz="UTC")
    assert result.annotations[0].timezone == "Europe/London"
    assert not result.annotations[0].inferred


def test_total_matches_job_count():
    jobs = [_make_job(f"j{i}") for i in range(4)]
    config = _make_config(_make_server(jobs=jobs))
    result = annotate_timezones(config)
    assert result.total == 4


def test_annotation_summary_contains_job_name():
    ann = TimezoneAnnotation(
        server="prod", job_name="nightly", command="cmd",
        schedule="0 0 * * *", timezone="UTC", inferred=False
    )
    assert "nightly" in ann.summary()
    assert "UTC" in ann.summary()
