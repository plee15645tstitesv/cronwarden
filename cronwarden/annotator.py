"""Annotator: attach inline notes/comments to cron jobs in a config."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from cronwarden.config import Config, CronJob


@dataclass
class Annotation:
    server: str
    job_name: str
    note: str

    def summary(self) -> str:
        return f"[{self.server}] {self.job_name}: {self.note}"


@dataclass
class AnnotationResult:
    annotations: List[Annotation] = field(default_factory=list)

    @property
    def has_annotations(self) -> bool:
        return len(self.annotations) > 0

    @property
    def total(self) -> int:
        return len(self.annotations)

    def for_server(self, server: str) -> List[Annotation]:
        return [a for a in self.annotations if a.server == server]

    def for_job(self, server: str, job_name: str) -> Optional[Annotation]:
        for a in self.annotations:
            if a.server == server and a.job_name == job_name:
                return a
        return None


def annotate_config(
    config: Config, notes: Dict[str, Dict[str, str]]
) -> AnnotationResult:
    """Attach notes to jobs. notes = {server_name: {job_name: note_text}}."""
    result = AnnotationResult()
    server_map = {s.name: s for s in config.servers}
    for server_name, job_notes in notes.items():
        server = server_map.get(server_name)
        if server is None:
            continue
        job_map = {j.name: j for j in server.jobs}
        for job_name, note in job_notes.items():
            if job_name in job_map:
                result.annotations.append(
                    Annotation(server=server_name, job_name=job_name, note=note)
                )
    return result


def list_annotations(result: AnnotationResult) -> List[str]:
    return [a.summary() for a in result.annotations]
