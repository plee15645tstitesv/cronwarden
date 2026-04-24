"""Tests for cronwarden.tagger_report."""

from cronwarden.config import Config, Server, CronJob
from cronwarden.tagger_report import build_tag_report, TagReportResult, TagStat


def _make_job(name: str, tags=None) -> CronJob:
    return CronJob(
        name=name,
        schedule="0 * * * *",
        command=f"run_{name}.sh",
        description=None,
        tags=tags or [],
    )


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def test_build_tag_report_returns_tag_report_result():
    server = Server(name="web", jobs=[_make_job("j1", ["backup"])])
    config = _make_config(server)
    result = build_tag_report(config)
    assert isinstance(result, TagReportResult)


def test_tag_report_counts_tags():
    server = Server(name="web", jobs=[
        _make_job("j1", ["backup"]),
        _make_job("j2", ["cleanup"]),
    ])
    config = _make_config(server)
    result = build_tag_report(config)
    assert result.total_tags == 2


def test_tag_report_counts_tagged_jobs():
    server = Server(name="web", jobs=[
        _make_job("j1", ["backup"]),
        _make_job("j2", ["backup"]),
        _make_job("j3", []),
    ])
    config = _make_config(server)
    result = build_tag_report(config)
    assert result.total_tagged_jobs == 2


def test_tag_report_counts_untagged_jobs():
    server = Server(name="web", jobs=[
        _make_job("j1", ["backup"]),
        _make_job("j2", []),
        _make_job("j3", []),
    ])
    config = _make_config(server)
    result = build_tag_report(config)
    assert result.untagged_job_count == 2


def test_tag_report_is_empty_when_no_tags():
    server = Server(name="web", jobs=[_make_job("j1")])
    config = _make_config(server)
    result = build_tag_report(config)
    assert result.is_empty()


def test_tag_report_most_used_tag():
    server = Server(name="web", jobs=[
        _make_job("j1", ["backup"]),
        _make_job("j2", ["backup"]),
        _make_job("j3", ["cleanup"]),
    ])
    config = _make_config(server)
    result = build_tag_report(config)
    assert result.most_used_tag() == "backup"


def test_tag_report_most_used_tag_none_when_empty():
    config = _make_config(Server(name="web", jobs=[]))
    result = build_tag_report(config)
    assert result.most_used_tag() is None


def test_tag_stat_summary_format():
    stat = TagStat(tag="backup", job_count=3, servers=["web", "db"])
    s = stat.summary()
    assert "backup" in s
    assert "3" in s
    assert "db" in s
    assert "web" in s


def test_tag_report_str_contains_tag():
    server = Server(name="web", jobs=[_make_job("j1", ["backup"])])
    config = _make_config(server)
    result = build_tag_report(config)
    assert "backup" in str(result)


def test_tag_report_multi_server():
    s1 = Server(name="web", jobs=[_make_job("j1", ["backup"])])
    s2 = Server(name="db", jobs=[_make_job("j2", ["backup"])])
    config = _make_config(s1, s2)
    result = build_tag_report(config)
    stat = next(s for s in result.stats if s.tag == "backup")
    assert "web" in stat.servers
    assert "db" in stat.servers
