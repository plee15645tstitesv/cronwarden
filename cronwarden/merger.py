"""Merge multiple config files into a single unified Config."""
from dataclasses import dataclass, field
from typing import List
from cronwarden.config import Config, Server, CronJob


@dataclass
class MergeConflict:
    server_name: str
    job_name: str
    reason: str

    def summary(self) -> str:
        return f"[{self.server_name}] {self.job_name}: {self.reason}"


@dataclass
class MergeResult:
    merged: Config
    conflicts: List[MergeConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    @property
    def total_servers(self) -> int:
        return len(self.merged.servers)

    @property
    def total_jobs(self) -> int:
        return sum(len(s.jobs) for s in self.merged.servers)


def merge_configs(configs: List[Config]) -> MergeResult:
    """Merge a list of Config objects into one, detecting duplicate job names per server."""
    server_map: dict[str, Server] = {}
    conflicts: List[MergeConflict] = []

    for config in configs:
        for server in config.servers:
            if server.name not in server_map:
                server_map[server.name] = Server(
                    name=server.name, host=server.host, jobs=[]
                )
            existing = server_map[server.name]
            existing_names = {j.name for j in existing.jobs}
            for job in server.jobs:
                if job.name in existing_names:
                    conflicts.append(
                        MergeConflict(
                            server_name=server.name,
                            job_name=job.name,
                            reason="duplicate job name across configs",
                        )
                    )
                else:
                    existing.jobs.append(job)
                    existing_names.add(job.name)

    merged = Config(servers=list(server_map.values()))
    return MergeResult(merged=merged, conflicts=conflicts)
