"""splitter.py — Split a config into per-server config objects."""

from dataclasses import dataclass, field
from typing import List, Dict

from cronwarden.config import Config, Server


@dataclass
class SplitEntry:
    server_name: str
    config: Config

    def summary(self) -> str:
        total = sum(len(s.jobs) for s in self.config.servers)
        return f"{self.server_name}: {total} job(s)"


@dataclass
class SplitResult:
    entries: List[SplitEntry] = field(default_factory=list)

    @property
    def has_entries(self) -> bool:
        return len(self.entries) > 0

    @property
    def total(self) -> int:
        return len(self.entries)

    def by_server(self, name: str) -> SplitEntry | None:
        for entry in self.entries:
            if entry.server_name == name:
                return entry
        return None


def split_config(config: Config) -> SplitResult:
    """Split a multi-server Config into individual single-server Config objects."""
    entries: List[SplitEntry] = []

    for server in config.servers:
        isolated_server = Server(
            name=server.name,
            host=server.host,
            jobs=list(server.jobs),
        )
        isolated_config = Config(servers=[isolated_server])
        entries.append(SplitEntry(server_name=server.name, config=isolated_config))

    return SplitResult(entries=entries)


def split_to_dict(config: Config) -> Dict[str, Config]:
    """Return a mapping of server name -> isolated Config."""
    result = split_config(config)
    return {entry.server_name: entry.config for entry in result.entries}
