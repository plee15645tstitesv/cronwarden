import pytest
from cronwarden.profiler import profile_config, _estimate_risk, ProfileResult, JobProfile
from cronwarden.config import CronJob, Server, Config


def _make_job(name="job1", command="/usr/bin/backup.sh", schedule="0 2 * * *",
              description=None, tags=None):
    return CronJob(name=name, command=command, schedule=schedule,
                   description=description, tags=tags or [])


def _make_config(jobs_per_server=None):
    if jobs_per_server is None:
        jobs_per_server = {"web-01": [_make_job()]}
    servers = [Server(name=name, jobs=jobs) for name, jobs in jobs_per_server.items()]
    return Config(servers=servers)


def test_profile_config_returns_profile_result():
    config = _make_config()
    result = profile_config(config)
    assert isinstance(result, ProfileResult)


def test_profile_config_total_jobs():
    config = _make_config({"web-01": [_make_job("a"), _make_job("b")], "db-01": [_make_job("c")]})
    result = profile_config(config)
    assert result.total() == 3


def test_profile_job_has_correct_server():
    config = _make_config({"web-01": [_make_job()]})
    result = profile_config(config)
    assert result.profiles[0].server == "web-01"


def test_high_risk_for_rm_command():
    job = _make_job(command="rm -rf /tmp/old")
    assert _estimate_risk(job) == "high"


def test_high_risk_for_drop_command():
    job = _make_job(command="mysql -e 'DROP TABLE logs'")
    assert _estimate_risk(job) == "high"


def test_medium_risk_for_sudo():
    job = _make_job(command="sudo systemctl restart nginx")
    assert _estimate_risk(job) == "medium"


def test_low_risk_for_safe_command():
    job = _make_job(command="/usr/bin/report.sh")
    assert _estimate_risk(job) == "low"


def test_by_risk_filters_correctly():
    config = _make_config({
        "web-01": [
            _make_job("safe", command="/bin/backup.sh"),
            _make_job("danger", command="rm -rf /logs"),
        ]
    })
    result = profile_config(config)
    assert len(result.by_risk("high")) == 1
    assert len(result.by_risk("low")) == 1


def test_has_description_true_when_set():
    config = _make_config({"web-01": [_make_job(description="Does something")]})
    result = profile_config(config)
    assert result.profiles[0].has_description is True


def test_has_description_false_when_missing():
    config = _make_config({"web-01": [_make_job(description=None)]})
    result = profile_config(config)
    assert result.profiles[0].has_description is False


def test_is_empty_true_for_empty_result():
    result = ProfileResult(profiles=[])
    assert result.is_empty() is True


def test_summary_contains_server_and_name():
    p = JobProfile(server="web-01", job_name="cleanup", schedule="0 * * * *",
                   command="/bin/clean", tags=[], has_description=True,
                   estimated_duration="unknown", risk_level="low")
    assert "web-01" in p.summary()
    assert "cleanup" in p.summary()
