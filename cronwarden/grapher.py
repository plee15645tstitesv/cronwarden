"""Graph cron job relationships by shared resources or timing overlap."""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from cronwarden.config import Config


@dataclass
class GraphEdge:
    source: str  # "server:job"
    target: str  # "server:job"
    reason: str  # e.g. "shared_command_token", "same_minute"

    def summary(self) -> str:
        return f"{self.source} -> {self.target} [{self.reason}]"


@dataclass
class GraphResult:
    nodes: List[str] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)

    @property
    def has_edges(self) -> bool:
        return len(self.edges) > 0

    @property
    def total_nodes(self) -> int:
        return len(self.nodes)

    @property
    def total_edges(self) -> int:
        return len(self.edges)


def _node_id(server_name: str, job_name: str) -> str:
    return f"{server_name}:{job_name}"


def _extract_minute(schedule: str) -> str:
    parts = schedule.strip().split()
    if len(parts) >= 1:
        return parts[0]
    return "*"


def _shared_tokens(cmd_a: str, cmd_b: str) -> bool:
    tokens_a = set(cmd_a.split())
    tokens_b = set(cmd_b.split())
    common = tokens_a & tokens_b
    meaningful = {t for t in common if len(t) > 3 and not t.startswith("-")}
    return len(meaningful) > 0


def build_graph(config: Config, mode: str = "command") -> GraphResult:
    """Build a relationship graph from a config.

    mode='command'  — link jobs sharing meaningful command tokens
    mode='timing'   — link jobs that fire in the same minute slot
    """
    result = GraphResult()
    all_jobs: List[Tuple[str, object]] = []

    for server in config.servers:
        for job in server.jobs:
            nid = _node_id(server.name, job.name)
            result.nodes.append(nid)
            all_jobs.append((server.name, job))

    for i in range(len(all_jobs)):
        for j in range(i + 1, len(all_jobs)):
            srv_a, job_a = all_jobs[i]
            srv_b, job_b = all_jobs[j]
            node_a = _node_id(srv_a, job_a.name)
            node_b = _node_id(srv_b, job_b.name)

            if mode == "command":
                if _shared_tokens(job_a.command, job_b.command):
                    result.edges.append(
                        GraphEdge(node_a, node_b, "shared_command_token")
                    )
            elif mode == "timing":
                min_a = _extract_minute(job_a.schedule)
                min_b = _extract_minute(job_b.schedule)
                if min_a == min_b and min_a != "*":
                    result.edges.append(
                        GraphEdge(node_a, node_b, f"same_minute:{min_a}")
                    )

    return result
