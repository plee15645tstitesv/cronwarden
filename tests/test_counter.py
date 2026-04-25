import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.counter import CountEntry, CountResult, count_config


def _make_job(name: str, schedule: str = "0 * * * *", user: str = "root") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=f"echo {name}", user=user)


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def test_count_config_returns_count_result():
    config = _make_config(Server(name="web", jobs=[_make_job("job1")]))
    result = count_config(config)
    assert isinstance(result, CountResult)


def test_count_result_total_matches_all_jobs():
    s1 = Server(name="web", jobs=[_make_job("j1"), _make_job("j2")])
    s2 = Server(name="db", jobs=[_make_job("j3")])
    result = count_config(_make_config(s1, s2))
    assert result.total == 3


def test_count_result_total_servers():
    s1 = Server(name="web", jobs=[_make_job("j1")])
    s2 = Server(name="db", jobs=[_make_job("j2")])
    result = count_config(_make_config(s1, s2))
    assert result.total_servers == 2


def test_count_result_is_empty_when_no_servers():
    result = count_config(_make_config())
    assert result.is_empty


def test_count_result_not_empty_when_servers_present():
    result = count_config(_make_config(Server(name="web", jobs=[_make_job("j1")])))
    assert not result.is_empty


def test_count_entry_by_schedule_groups_correctly():
    jobs = [
        _make_job("j1", schedule="0 * * * *"),
        _make_job("j2", schedule="0 * * * *"),
        _make_job("j3", schedule="@daily"),
    ]
    result = count_config(_make_config(Server(name="web", jobs=jobs)))
    entry = result.entries[0]
    assert entry.by_schedule["0 * * * *"] == 2
    assert entry.by_schedule["@daily"] == 1


def test_count_entry_by_user_groups_correctly():
    jobs = [
        _make_job("j1", user="root"),
        _make_job("j2", user="root"),
        _make_job("j3", user="deploy"),
    ]
    result = count_config(_make_config(Server(name="web", jobs=jobs)))
    entry = result.entries[0]
    assert entry.by_user["root"] == 2
    assert entry.by_user["deploy"] == 1


def test_count_entry_summary_contains_server_name():
    entry = CountEntry(server="myserver", total_jobs=5, by_schedule={}, by_user={})
    assert "myserver" in entry.summary()
    assert "5" in entry.summary()


def test_grand_total_by_schedule_merges_across_servers():
    s1 = Server(name="web", jobs=[_make_job("j1", schedule="@daily")])
    s2 = Server(name="db", jobs=[_make_job("j2", schedule="@daily"), _make_job("j3", schedule="@hourly")])
    result = count_config(_make_config(s1, s2))
    grand = result.grand_total_by_schedule()
    assert grand["@daily"] == 2
    assert grand["@hourly"] == 1


def test_user_defaults_to_unknown_when_none():
    job = CronJob(name="j1", schedule="@daily", command="echo hi", user=None)
    result = count_config(_make_config(Server(name="web", jobs=[job])))
    entry = result.entries[0]
    assert "unknown" in entry.by_user
