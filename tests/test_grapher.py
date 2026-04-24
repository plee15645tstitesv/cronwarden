"""Tests for cronwarden.grapher."""
import pytest
from cronwarden.grapher import build_graph, GraphEdge, GraphResult, _node_id
from cronwarden.config import Config, Server, CronJob


def _make_job(name: str, schedule: str = "0 * * * *", command: str = "echo hello") -> CronJob:
    return CronJob(name=name, schedule=schedule, command=command)


def _make_config(*servers: Server) -> Config:
    return Config(servers=list(servers))


def _make_server(name: str, jobs) -> Server:
    return Server(name=name, host="localhost", jobs=jobs)


# --- GraphResult ---

def test_graph_result_has_edges_false_when_empty():
    r = GraphResult(nodes=["a"], edges=[])
    assert r.has_edges is False


def test_graph_result_has_edges_true_when_populated():
    r = GraphResult(nodes=["a", "b"], edges=[GraphEdge("a", "b", "test")])
    assert r.has_edges is True


def test_graph_result_total_nodes():
    r = GraphResult(nodes=["a", "b", "c"], edges=[])
    assert r.total_nodes == 3


def test_graph_result_total_edges():
    r = GraphResult(nodes=["a", "b"], edges=[GraphEdge("a", "b", "x"), GraphEdge("b", "a", "y")])
    assert r.total_edges == 2


# --- build_graph nodes ---

def test_build_graph_returns_graph_result():
    cfg = _make_config(_make_server("s1", [_make_job("j1")]))
    result = build_graph(cfg)
    assert isinstance(result, GraphResult)


def test_build_graph_nodes_include_all_jobs():
    jobs = [_make_job("backup"), _make_job("cleanup")]
    cfg = _make_config(_make_server("web", jobs))
    result = build_graph(cfg)
    assert "web:backup" in result.nodes
    assert "web:cleanup" in result.nodes


def test_build_graph_empty_config_has_no_nodes():
    cfg = _make_config()
    result = build_graph(cfg)
    assert result.total_nodes == 0
    assert result.total_edges == 0


# --- command mode ---

def test_command_mode_links_shared_token_jobs():
    j1 = _make_job("backup-db", command="/usr/bin/mysqldump mydb")
    j2 = _make_job("verify-db", command="/usr/bin/mysqlcheck mydb")
    cfg = _make_config(_make_server("prod", [j1, j2]))
    result = build_graph(cfg, mode="command")
    assert result.has_edges
    assert any(e.reason == "shared_command_token" for e in result.edges)


def test_command_mode_no_edge_for_unrelated_commands():
    j1 = _make_job("task-a", command="/bin/alpha run")
    j2 = _make_job("task-b", command="/bin/beta execute")
    cfg = _make_config(_make_server("prod", [j1, j2]))
    result = build_graph(cfg, mode="command")
    assert not result.has_edges


def test_command_mode_ignores_short_tokens():
    j1 = _make_job("a", command="ls -la")
    j2 = _make_job("b", command="ls -lh")
    cfg = _make_config(_make_server("s", [j1, j2]))
    result = build_graph(cfg, mode="command")
    # 'ls' is 2 chars, flags start with '-'; no meaningful shared token
    assert not result.has_edges


# --- timing mode ---

def test_timing_mode_links_same_minute_jobs():
    j1 = _make_job("j1", schedule="15 * * * *")
    j2 = _make_job("j2", schedule="15 2 * * *")
    cfg = _make_config(_make_server("s", [j1, j2]))
    result = build_graph(cfg, mode="timing")
    assert result.has_edges
    assert any("same_minute:15" in e.reason for e in result.edges)


def test_timing_mode_no_edge_for_wildcard_minute():
    j1 = _make_job("j1", schedule="* * * * *")
    j2 = _make_job("j2", schedule="* 1 * * *")
    cfg = _make_config(_make_server("s", [j1, j2]))
    result = build_graph(cfg, mode="timing")
    assert not result.has_edges


def test_timing_mode_no_edge_different_minutes():
    j1 = _make_job("j1", schedule="10 * * * *")
    j2 = _make_job("j2", schedule="20 * * * *")
    cfg = _make_config(_make_server("s", [j1, j2]))
    result = build_graph(cfg, mode="timing")
    assert not result.has_edges


# --- edge summary ---

def test_graph_edge_summary_format():
    e = GraphEdge("srv:job_a", "srv:job_b", "shared_command_token")
    s = e.summary()
    assert "srv:job_a" in s
    assert "srv:job_b" in s
    assert "shared_command_token" in s
