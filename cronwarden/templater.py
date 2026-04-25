"""Generate cron job config templates from common patterns."""
from dataclasses import dataclass, field
from typing import List, Optional

COMMON_TEMPLATES = {
    "daily-midnight": {"schedule": "0 0 * * *", "description": "Runs daily at midnight"},
    "hourly": {"schedule": "0 * * * *", "description": "Runs every hour"},
    "weekly-sunday": {"schedule": "0 0 * * 0", "description": "Runs weekly on Sunday"},
    "monthly-first": {"schedule": "0 0 1 * *", "description": "Runs on the first of each month"},
    "every-5-minutes": {"schedule": "*/5 * * * *", "description": "Runs every 5 minutes"},
    "weekdays-9am": {"schedule": "0 9 * * 1-5", "description": "Runs weekdays at 9am"},
}


@dataclass
class TemplateResult:
    name: str
    schedule: str
    description: str
    server: str
    command: str
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "schedule": self.schedule,
            "description": self.description,
            "command": self.command,
            "tags": self.tags,
        }

    def to_yaml_block(self) -> str:
        lines = [
            f"      - name: {self.name}",
            f"        schedule: \"{self.schedule}\"",
            f"        command: {self.command}",
            f"        description: {self.description}",
        ]
        if self.tags:
            lines.append("        tags:")
            for tag in self.tags:
                lines.append(f"          - {tag}")
        return "\n".join(lines)


def list_templates() -> List[str]:
    """Return a sorted list of available template names."""
    return sorted(COMMON_TEMPLATES.keys())


def get_template_info(template_name: str) -> dict:
    """Return the schedule and description for a named template.

    Raises ValueError if the template name is not found.
    """
    if template_name not in COMMON_TEMPLATES:
        raise ValueError(
            f"Unknown template '{template_name}'. Available: {', '.join(sorted(COMMON_TEMPLATES))}"
        )
    return dict(COMMON_TEMPLATES[template_name])


def generate_template(
    template_name: str,
    job_name: str,
    command: str,
    server: str,
    tags: Optional[List[str]] = None,
) -> TemplateResult:
    """Generate a TemplateResult from a named template and job parameters.

    Args:
        template_name: One of the keys in COMMON_TEMPLATES.
        job_name: The name to assign to the cron job.
        command: The shell command the cron job will execute.
        server: The server on which the job will run.
        tags: Optional list of tags to attach to the job.

    Returns:
        A populated TemplateResult instance.

    Raises:
        ValueError: If template_name is not a recognised template.
    """
    tmpl = get_template_info(template_name)
    return TemplateResult(
        name=job_name,
        schedule=tmpl["schedule"],
        description=tmpl["description"],
        server=server,
        command=command,
        tags=tags or [],
    )
