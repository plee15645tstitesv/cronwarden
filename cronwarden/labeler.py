from dataclasses import dataclass, field
from typing import List, Dict
from cronwarden.config import Config, CronJob


@dataclass
class LabeledJob:
    server: str
    job: CronJob
    labels: List[str]

    def summary(self) -> str:
        label_str = ", ".join(self.labels) if self.labels else "(none)"
        return f"{self.server}/{self.job.name}: [{label_str}]"


@dataclass
class LabelResult:
    labeled: List[LabeledJob] = field(default_factory=list)

    def has_labels(self) -> bool:
        return len(self.labeled) > 0

    def total(self) -> int:
        return len(self.labeled)

    def by_label(self) -> Dict[str, List[LabeledJob]]:
        result: Dict[str, List[LabeledJob]] = {}
        for lj in self.labeled:
            for label in lj.labels:
                result.setdefault(label, []).append(lj)
        return result


_LABEL_RULES = [
    ("frequent", lambda job: job.schedule.startswith("*/") or job.schedule == "* * * * *"),
    ("daily", lambda job: job.schedule.endswith("* * *") and job.schedule.split()[0].isdigit()),
    ("weekly", lambda job: job.schedule.split()[-1] not in ("*",) and len(job.schedule.split()) == 5 and job.schedule.split()[-1].isdigit()),
    ("uses-sudo", lambda job: "sudo" in job.command),
    ("long-running", lambda job: any(t in job.command for t in ["rsync", "pg_dump", "mysqldump", "tar"])),
    ("tagged", lambda job: bool(job.tags)),
    ("undocumented", lambda job: not job.description),
]


def label_config(config: Config) -> LabelResult:
    result = LabelResult()
    for server in config.servers:
        for job in server.jobs:
            labels = [name for name, rule in _LABEL_RULES if rule(job)]
            result.labeled.append(LabeledJob(server=server.name, job=job, labels=labels))
    return result
