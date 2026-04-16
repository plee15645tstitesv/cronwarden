import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.tracer import trace_jobs, TraceResult, TraceMatch


def _make_job(name, command, schedule="0 * * * *", tags=None):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [])


def _make_config():
    s1 = Server(name="web", host="web.example.com", jobs=[
        _make_job("backup", "/usr/bin/backup.sh"),
        _make_job("cleanup", "rm -rf /tmp/old"),
    ])
    s2 = Server(name="db", host="db.example.com", jobs=[
        _make_job("dump", "/usr/bin/pg_dump mydb", schedule="30 2 * * *"),
        _make_job("vacuum", "/usr/bin/vacuumdb"),
    ])
    return Config(servers=[s1, s2])


def test_trace_returns_trace_result():
    config = _make_config()
    result = trace_jobs(config, r"backup")
    assert isinstance(result, TraceResult)


def test_trace_matches_command_by_default():
    config = _make_config()
    result = trace_jobs(config, r"backup")
    assert result.has_matches
    assert result.total == 2
    names = [m.job.name for m in result.matches]
    assert "backup" in names
    assert "dump" not in names


def test_trace_no_matches():
    config = _make_config()
    result = trace_jobs(config, r"nonexistent_pattern_xyz")
    assert not result.has_matches
    assert result.total == 0


def test_trace_by_schedule():
    config = _make_config()
    result = trace_jobs(config, r"30 2", field="schedule")
    assert result.has_matches
    assert result.total == 1
    assert result.matches[0].job.name == "dump"


def test_trace_by_name():
    config = _make_config()
    result = trace_jobs(config, r"^clean", field="name")
    assert result.has_matches
    assert result.matches[0].job.name == "cleanup"


def test_trace_invalid_field_raises():
    config = _make_config()
    with pytest.raises(ValueError, match="Unsupported trace field"):
        trace_jobs(config, r".*", field="description")


def test_trace_invalid_regex_raises():
    config = _make_config()
    with pytest.raises(ValueError, match="Invalid regex"):
        trace_jobs(config, r"[unclosed")


def test_trace_result_str_no_matches():
    result = TraceResult(pattern="xyz", field="command", matches=[])
    assert "No jobs matched" in str(result)


def test_trace_result_str_with_matches():
    config = _make_config()
    result = trace_jobs(config, r"backup")
    output = str(result)
    assert "backup" in output
    assert "matched" in output


def test_trace_match_summary_contains_server():
    job = _make_job("myjob", "echo hi")
    match = TraceMatch(server="prod", job=job)
    assert "prod" in match.summary()
    assert "myjob" in match.summary()
