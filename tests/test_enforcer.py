import pytest
from cronwarden.enforcer import enforce, EnforcementResult
from cronwarden.config import Config, Server, CronJob


def _make_job(name="backup", command="/usr/bin/backup.sh", tags=None, description=None):
    return CronJob(name=name, schedule="0 2 * * *", command=command, tags=tags, description=description)


def _make_config(*servers):
    return Config(servers=list(servers))


def _make_server(name="prod", jobs=None):
    return Server(name=name, host="localhost", jobs=jobs or [])


def test_enforce_returns_enforcement_result():
    config = _make_config(_make_server(jobs=[_make_job()]))
    result = enforce(config)
    assert isinstance(result, EnforcementResult)


def test_no_rules_no_violations():
    config = _make_config(_make_server(jobs=[_make_job()]))
    result = enforce(config)
    assert not result.has_violations
    assert result.total == 0


def test_required_tag_present_no_violation():
    job = _make_job(tags=["backup", "critical"])
    config = _make_config(_make_server(jobs=[job]))
    result = enforce(config, required_tags=["backup"])
    assert not result.has_violations


def test_required_tag_missing_creates_violation():
    job = _make_job(tags=["cleanup"])
    config = _make_config(_make_server(jobs=[job]))
    result = enforce(config, required_tags=["backup"])
    assert result.has_violations
    assert result.total == 1
    assert result.violations[0].rule == "required-tags"


def test_required_tag_missing_includes_job_and_server():
    job = _make_job(name="myjob", tags=[])
    config = _make_config(_make_server(name="web", jobs=[job]))
    result = enforce(config, required_tags=["owner"])
    v = result.violations[0]
    assert v.server == "web"
    assert v.job_name == "myjob"


def test_forbidden_command_triggers_violation():
    job = _make_job(command="sudo rm -rf /tmp")
    config = _make_config(_make_server(jobs=[job]))
    result = enforce(config, forbidden_commands=["rm -rf"])
    assert result.has_violations
    assert result.violations[0].rule == "forbidden-command"


def test_safe_command_no_violation():
    job = _make_job(command="/usr/bin/backup.sh")
    config = _make_config(_make_server(jobs=[job]))
    result = enforce(config, forbidden_commands=["rm -rf"])
    assert not result.has_violations


def test_multiple_violations_across_servers():
    j1 = _make_job(name="j1", tags=[], command="sudo rm -rf /var")
    j2 = _make_job(name="j2", tags=[])
    s1 = _make_server(name="s1", jobs=[j1])
    s2 = _make_server(name="s2", jobs=[j2])
    config = _make_config(s1, s2)
    result = enforce(config, required_tags=["owner"], forbidden_commands=["rm -rf"])
    assert result.total >= 3


def test_str_no_violations():
    config = _make_config(_make_server(jobs=[_make_job(tags=["backup"])]))
    result = enforce(config, required_tags=["backup"])
    assert "comply" in str(result)


def test_str_with_violations():
    job = _make_job(tags=[])
    config = _make_config(_make_server(jobs=[job]))
    result = enforce(config, required_tags=["owner"])
    assert "violation" in str(result)
