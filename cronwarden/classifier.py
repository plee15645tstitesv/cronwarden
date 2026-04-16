"""Classify cron jobs into categories based on schedule patterns and command heuristics."""

from dataclasses import dataclass, field
from typing import List, Dict
from cronwarden.config import Config, CronJob

CATEGORIES = {
    "backup": ["backup", "dump", "rsync", "tar", "pg_dump", "mysqldump"],
    "cleanup": ["clean", "purge", "delete", "remove", "prune", "rm "],
    "monitoring": ["check", "monitor", "alert", "ping", "health", "status"],
    "reporting": ["report", "export", "send", "mail", "email", "notify"],
    "maintenance": ["update", "upgrade", "migrate", "reindex", "vacuum", "rotate"],
}


@dataclass
class ClassifiedJob:
    server: str
    job: CronJob
    category: str

    def summary(self) -> str:
        return f"[{self.category}] {self.server}/{self.job.name}: {self.job.command}"


@dataclass
class ClassificationResult:
    classified: List[ClassifiedJob] = field(default_factory=list)
    unclassified: List[tuple] = field(default_factory=list)

    def has_unclassified(self) -> bool:
        return len(self.unclassified) > 0

    def total(self) -> int:
        return len(self.classified) + len(self.unclassified)

    def by_category(self) -> Dict[str, List[ClassifiedJob]]:
        result: Dict[str, List[ClassifiedJob]] = {}
        for cj in self.classified:
            result.setdefault(cj.category, []).append(cj)
        return result


def _detect_category(job: CronJob) -> str:
    command_lower = job.command.lower()
    name_lower = job.name.lower()
    combined = command_lower + " " + name_lower
    for category, keywords in CATEGORIES.items():
        if any(kw in combined for kw in keywords):
            return category
    return ""


def classify_config(config: Config) -> ClassificationResult:
    result = ClassificationResult()
    for server in config.servers:
        for job in server.jobs:
            category = _detect_category(job)
            if category:
                result.classified.append(ClassifiedJob(server.name, job, category))
            else:
                result.unclassified.append((server.name, job))
    return result
