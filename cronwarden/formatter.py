"""Output formatters for cronwarden audit results."""

from __future__ import annotations

import json
from typing import List

from cronwarden.reporter import ServerReport


def format_text(reports: List[ServerReport]) -> str:
    """Render audit results as human-readable text."""
    lines: List[str] = []

    for server_report in reports:
        lines.append(f"Server: {server_report.server_name}")
        lines.append("-" * (len(server_report.server_name) + 8))

        for job_report in server_report.job_reports:
            icon = job_report.status_icon()
            summary = job_report.summary_line()
            lines.append(f"  {icon}  {summary}")

            for issue in job_report.result.issues:
                lines.append(f"       • {issue}")

        total = server_report.total()
        lines.append(f"  Total: {total} job(s)")
        lines.append("")

    return "\n".join(lines).rstrip()


def format_json(reports: List[ServerReport]) -> str:
    """Render audit results as JSON."""
    data = []

    for server_report in reports:
        server_data = {
            "server": server_report.server_name,
            "total_jobs": server_report.total(),
            "jobs": [
                {
                    "name": jr.job_name,
                    "schedule": jr.schedule,
                    "valid": jr.result.valid,
                    "issues": jr.result.issues,
                    "description": jr.description,
                }
                for jr in server_report.job_reports
            ],
        }
        data.append(server_data)

    return json.dumps(data, indent=2)


def format_markdown(reports: List[ServerReport]) -> str:
    """Render audit results as a Markdown table per server."""
    lines: List[str] = []

    for server_report in reports:
        lines.append(f"## Server: `{server_report.server_name}`\n")
        lines.append("| Status | Job | Schedule | Description | Issues |")
        lines.append("|--------|-----|----------|-------------|--------|")

        for jr in server_report.job_reports:
            icon = jr.status_icon()
            issues = "; ".join(jr.result.issues) if jr.result.issues else "—"
            desc = jr.description or "—"
            lines.append(
                f"| {icon} | `{jr.job_name}` | `{jr.schedule}` | {desc} | {issues} |"
            )

        lines.append("")

    return "\n".join(lines).rstrip()


FORMATS = {
    "text": format_text,
    "json": format_json,
    "markdown": format_markdown,
}


def render(reports: List[ServerReport], fmt: str = "text") -> str:
    """Dispatch to the requested formatter.

    Raises ValueError for unknown formats.
    """
    if fmt not in FORMATS:
        raise ValueError(
            f"Unknown format {fmt!r}. Choose from: {', '.join(FORMATS)}"
        )
    return FORMATS[fmt](reports)
