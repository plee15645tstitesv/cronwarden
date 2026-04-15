"""Export cron job configs to various formats (CSV, TOML-like table)."""
from __future__ import annotations

import csv
import io
from typing import List

from cronwarden.config import Config
from cronwarden.validator import validate_job


def export_csv(config: Config) -> str:
    """Export all jobs across all servers to a CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["server", "job_name", "schedule", "command", "user", "tags", "description", "valid"])

    for server in config.servers:
        for job in server.jobs:
            result = validate_job(job)
            tags = "|".join(job.tags) if job.tags else ""
            writer.writerow([
                server.name,
                job.name,
                job.schedule,
                job.command,
                job.user or "",
                tags,
                job.description or "",
                "yes" if result.is_valid else "no",
            ])

    return output.getvalue()


def export_table(config: Config) -> str:
    """Export all jobs as a plain-text aligned table."""
    rows: List[List[str]] = []
    header = ["SERVER", "JOB", "SCHEDULE", "COMMAND", "VALID"]
    rows.append(header)

    for server in config.servers:
        for job in server.jobs:
            result = validate_job(job)
            rows.append([
                server.name,
                job.name,
                job.schedule,
                job.command[:40] + ("..." if len(job.command) > 40 else ""),
                "✓" if result.is_valid else "✗",
            ])

    if len(rows) == 1:
        return "No jobs found."

    col_widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
    sep = "  ".join("-" * w for w in col_widths)
    lines = []
    for idx, row in enumerate(rows):
        lines.append("  ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)))
        if idx == 0:
            lines.append(sep)
    return "\n".join(lines)
