"""Compare two configs and produce a human-readable comparison report."""

from dataclasses import dataclass, field
from typing import List, Optional
from cronwarden.config import Config


@dataclass
class JobComparison:
    server: str
    job_name: str
    field: str
    left_value: Optional[str]
    right_value: Optional[str]

    def summary(self) -> str:
        return (
            f"[{self.server}] {self.job_name}.{self.field}: "
            f"{self.left_value!r} -> {self.right_value!r}"
        )


@dataclass
class ComparisonResult:
    left_label: str
    right_label: str
    differences: List[JobComparison] = field(default_factory=list)

    def has_differences(self) -> bool:
        return len(self.differences) > 0

    def total(self) -> int:
        return len(self.differences)

    def __str__(self) -> str:
        if not self.has_differences():
            return f"No differences between '{self.left_label}' and '{self.right_label}'."
        lines = [
            f"Comparing '{self.left_label}' vs '{self.right_label}': {self.total()} difference(s)"
        ]
        for diff in self.differences:
            lines.append(f"  {diff.summary()}")
        return "\n".join(lines)


COMPARED_FIELDS = ["schedule", "command", "description"]


def compare_configs(
    left: Config,
    right: Config,
    left_label: str = "left",
    right_label: str = "right",
) -> ComparisonResult:
    """Compare two Config objects field-by-field for each matching job."""
    result = ComparisonResult(left_label=left_label, right_label=right_label)

    left_index = {
        (server.name, job.name): job
        for server in left.servers
        for job in server.jobs
    }
    right_index = {
        (server.name, job.name): job
        for server in right.servers
        for job in server.jobs
    }

    all_keys = sorted(set(left_index) | set(right_index))

    for server_name, job_name in all_keys:
        left_job = left_index.get((server_name, job_name))
        right_job = right_index.get((server_name, job_name))

        for f in COMPARED_FIELDS:
            lv = getattr(left_job, f, None) if left_job else None
            rv = getattr(right_job, f, None) if right_job else None
            if lv != rv:
                result.differences.append(
                    JobComparison(
                        server=server_name,
                        job_name=job_name,
                        field=f,
                        left_value=str(lv) if lv is not None else None,
                        right_value=str(rv) if rv is not None else None,
                    )
                )

    return result
