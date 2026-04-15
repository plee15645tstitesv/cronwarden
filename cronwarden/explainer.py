"""Human-readable explanations for cron schedule expressions."""

from typing import Optional

DAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

SPECIAL_SCHEDULES = {
    "@yearly":   "Once a year, at midnight on January 1st",
    "@annually": "Once a year, at midnight on January 1st",
    "@monthly":  "Once a month, at midnight on the 1st",
    "@weekly":   "Once a week, at midnight on Sunday",
    "@daily":    "Once a day, at midnight",
    "@midnight": "Once a day, at midnight",
    "@hourly":   "Once an hour, at the start of the hour",
    "@reboot":   "Once, at system startup",
}


def _explain_field(value: str, unit: str, names: Optional[list] = None) -> str:
    if value == "*":
        return f"every {unit}"
    if value.startswith("*/"):
        step = value[2:]
        return f"every {step} {unit}s"
    if "-" in value and "/" not in value:
        parts = value.split("-")
        start = names[int(parts[0])] if names else parts[0]
        end = names[int(parts[1])] if names else parts[1]
        return f"from {start} to {end}"
    if "," in value:
        items = value.split(",")
        labels = [names[int(i)] if names else i for i in items]
        return "on " + ", ".join(labels)
    label = names[int(value)] if names else value
    return f"at {unit} {label}"


def explain_schedule(schedule: str) -> str:
    """Return a human-readable description of a cron schedule string."""
    schedule = schedule.strip()
    if schedule in SPECIAL_SCHEDULES:
        return SPECIAL_SCHEDULES[schedule]

    parts = schedule.split()
    if len(parts) != 5:
        return "Invalid or unrecognised schedule expression."

    minute, hour, dom, month, dow = parts

    segments = []
    segments.append(_explain_field(minute, "minute"))
    segments.append(_explain_field(hour, "hour"))
    if dom != "*":
        segments.append(_explain_field(dom, "day-of-month"))
    if month != "*":
        segments.append(_explain_field(month, "month", MONTH_NAMES))
    if dow != "*":
        segments.append(_explain_field(dow, "day-of-week", DAY_NAMES))

    return "Runs " + ", ".join(segments) + "."
