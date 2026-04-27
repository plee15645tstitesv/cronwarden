import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.tagger_stats import compute_tag_stats, TagStatsResult, TagUsageStat


def _make_job(name: str, tags=None) -> CronJob:
    return CronJob(
        name=name,
        schedule="0 * * * *",
        command=f"run_{name}.sh",
        description=None,
        tags=tags or [],
    )


def _make_config(*servers) -> Config:
    return Config(servers=list(servers))


def _make_server(name: str, jobs) -> Server:
    return Server(name=name, host=f"{name}.example.com", jobs=jobs)


def test_compute_tag_stats_returns_tag_stats_result():
    config = _make_config(_make_server("s1", [_make_job("j1", ["backup"])]))
    result = compute_tag_stats(config)
    assert isinstance(result, TagStatsResult)


def test_empty_config_returns_empty_result():
    config = _make_config(_make_server("s1", [_make_job("j1", [])]))
    result = compute_tag_stats(config)
    assert result.is_empty()
    assert result.total_tags() == 0


def test_single_tag_counted_correctly():
    config = _make_config(
        _make_server("s1", [_make_job("j1", ["backup"]), _make_job("j2", ["backup"])])
    )
    result = compute_tag_stats(config)
    assert result.total_tags() == 1
    assert result.stats[0].job_count == 2


def test_multiple_tags_all_present():
    config = _make_config(
        _make_server("s1", [
            _make_job("j1", ["backup", "nightly"]),
            _make_job("j2", ["cleanup"]),
        ])
    )
    result = compute_tag_stats(config)
    tag_names = {s.tag for s in result.stats}
    assert "backup" in tag_names
    assert "nightly" in tag_names
    assert "cleanup" in tag_names


def test_most_used_tag_is_correct():
    config = _make_config(
        _make_server("s1", [
            _make_job("j1", ["backup"]),
            _make_job("j2", ["backup"]),
            _make_job("j3", ["cleanup"]),
        ])
    )
    result = compute_tag_stats(config)
    assert result.most_used().tag == "backup"


def test_least_used_tag_is_correct():
    config = _make_config(
        _make_server("s1", [
            _make_job("j1", ["backup"]),
            _make_job("j2", ["backup"]),
            _make_job("j3", ["cleanup"]),
        ])
    )
    result = compute_tag_stats(config)
    assert result.least_used().tag == "cleanup"


def test_tag_server_count_across_multiple_servers():
    config = _make_config(
        _make_server("s1", [_make_job("j1", ["backup"])]),
        _make_server("s2", [_make_job("j2", ["backup"])]),
    )
    result = compute_tag_stats(config)
    stat = result.stats[0]
    assert stat.server_count == 2
    assert "s1" in stat.servers
    assert "s2" in stat.servers


def test_tags_used_on_multiple_servers_filter():
    config = _make_config(
        _make_server("s1", [_make_job("j1", ["shared", "local"])])
        ,
        _make_server("s2", [_make_job("j2", ["shared"])])
    )
    result = compute_tag_stats(config)
    multi = result.tags_used_on_multiple_servers()
    assert len(multi) == 1
    assert multi[0].tag == "shared"


def test_most_used_returns_none_when_empty():
    config = _make_config(_make_server("s1", []))
    result = compute_tag_stats(config)
    assert result.most_used() is None
    assert result.least_used() is None


def test_tag_stat_summary_format():
    stat = TagUsageStat(tag="backup", job_count=3, server_count=2, servers=["s1", "s2"])
    assert "backup" in stat.summary()
    assert "3" in stat.summary()
    assert "2" in stat.summary()
