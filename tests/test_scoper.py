"""Tests for cronwarden.scoper."""
import pytest
from cronwarden.config import CronJob, Server, Config
from cronwarden.scoper import ScopeResult, ScopedJob, _extract_scope, analyze_scope


def _make_job(name: str, command: str, schedule: str = "0 * * * *") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def _make_server(name: str, *jobs: CronJob) -> Server:
    return Server(name=name, jobs=list(jobs))


# --- ScopeResult unit tests ---

def test_scope_result_is_empty_when_no_entries():
    result = ScopeResult(entries=[])
    assert result.is_empty


def test_scope_result_total_zero_when_empty():
    result = ScopeResult(entries=[])
    assert result.total == 0


def test_scope_result_has_overlaps_false_when_no_overlaps():
    entry = ScopedJob(server="s", job_name="j", command="echo hi", scope="hi")
    result = ScopeResult(entries=[entry])
    assert not result.has_overlaps


def test_scope_result_has_overlaps_true_when_overlap():
    entry = ScopedJob(server="s", job_name="j", command="echo hi", scope="hi",
                     overlap_with=["s/j2"])
    result = ScopeResult(entries=[entry])
    assert result.has_overlaps


def test_overlapping_entries_returns_only_flagged():
    e1 = ScopedJob(server="s", job_name="j1", command="cmd", scope="/data",
                   overlap_with=["s/j2"])
    e2 = ScopedJob(server="s", job_name="j2", command="cmd", scope="/data")
    result = ScopeResult(entries=[e1, e2])
    assert result.overlapping_entries() == [e1]


# --- _extract_scope tests ---

def test_extract_scope_picks_path():
    assert _extract_scope("rsync /var/data /backup") == "/var/data"


def test_extract_scope_picks_second_token_when_no_path():
    assert _extract_scope("python backup.py") == "backup.py"


def test_extract_scope_skips_flags():
    assert _extract_scope("tar -czf /tmp/archive.tar /data") == "/tmp/archive.tar"


def test_extract_scope_falls_back_to_first_token():
    assert _extract_scope("cleanup") == "cleanup"


# --- analyze_scope integration tests ---

def test_analyze_scope_returns_scope_result():
    cfg = _make_config(_make_server("web", _make_job("j1", "echo hello")))
    result = analyze_scope(cfg)
    assert isinstance(result, ScopeResult)


def test_analyze_scope_total_matches_all_jobs():
    cfg = _make_config(
        _make_server("s1",
                     _make_job("j1", "rsync /data /backup"),
                     _make_job("j2", "python clean.py")),
        _make_server("s2",
                     _make_job("j3", "bash /opt/run.sh")),
    )
    result = analyze_scope(cfg)
    assert result.total == 3


def test_analyze_scope_detects_overlap_across_servers():
    cfg = _make_config(
        _make_server("s1", _make_job("j1", "rsync /data /backup")),
        _make_server("s2", _make_job("j2", "rsync /data /mirror")),
    )
    result = analyze_scope(cfg)
    assert result.has_overlaps


def test_analyze_scope_no_overlap_for_unique_scopes():
    cfg = _make_config(
        _make_server("s1", _make_job("j1", "rsync /alpha /backup")),
        _make_server("s2", _make_job("j2", "rsync /beta /backup")),
    )
    result = analyze_scope(cfg)
    # /alpha and /beta are different scopes; no overlap
    overlapping = result.overlapping_entries()
    scope_tokens = {e.scope for e in overlapping}
    assert "/alpha" not in scope_tokens or "/beta" not in scope_tokens


def test_scoped_job_summary_with_overlap():
    entry = ScopedJob(server="prod", job_name="backup", command="rsync /data",
                      scope="/data", overlap_with=["staging/backup"])
    assert "overlap" in entry.summary().lower() or "staging/backup" in entry.summary()


def test_scoped_job_summary_no_overlap():
    entry = ScopedJob(server="prod", job_name="backup", command="rsync /data",
                      scope="/data")
    assert "overlap" not in entry.summary().lower()
