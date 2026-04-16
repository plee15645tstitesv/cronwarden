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
    return list(COMMON_TEMPLATES.keys())


def generate_template(
    template_name: str,
    job_name: str,
    command: str,
    server: str,
    tags: Optional[List[str]] = None,
) -> TemplateResult:
    if template_name not in COMMON_TEMPLATES:
        raise ValueError(
            f"Unknown template '{template_name}'. Available: {', '.join(COMMON_TEMPLATES)}"
        )
    tmpl = COMMON_TEMPLATES[template_name]
    return TemplateResult(
        name=job_name,
        schedule=tmpl["schedule"],
        description=tmpl["description"],
        server=server,
        command=command,
        tags=tags or [],
    )
