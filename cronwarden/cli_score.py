"""CLI command to score cron jobs in a config file."""
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.scorer import score_config


def _format_text(result) -> str:
    lines = []
    for s in result.scores:
        tag = "[OK]" if s.score >= 75 else "[WARN]" if s.score >= 50 else "[FAIL]"
        lines.append(f"  {tag} {s.summary()}")
        for reason in s.reasons:
            lines.append(f"       - {reason}")
    lines.append("")
    lines.append(f"Average score: {result.average_score()}/100")
    healthy = "healthy" if result.is_healthy() else "unhealthy"
    lines.append(f"Overall status: {healthy}")
    if result.lowest():
        lines.append(f"Lowest:  {result.lowest().summary()}")
    if result.highest():
        lines.append(f"Highest: {result.highest().summary()}")
    return "\n".join(lines)


def _format_json(result) -> str:
    data = {
        "average_score": result.average_score(),
        "is_healthy": result.is_healthy(),
        "scores": [
            {
                "server": s.server_name,
                "job": s.job_name,
                "score": s.score,
                "grade": s.grade(),
                "reasons": s.reasons,
            }
            for s in result.scores
        ],
    }
    return json.dumps(data, indent=2)


def run_score(args) -> int:
    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        return 1

    result = score_config(config)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    return 0 if result.is_healthy() else 1
