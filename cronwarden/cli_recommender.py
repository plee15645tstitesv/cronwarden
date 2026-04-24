import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.recommender import recommend, RecommendationResult


def _format_text(result: RecommendationResult) -> str:
    if not result.has_recommendations:
        return "No recommendations. All jobs look good!\n"
    lines = [f"Recommendations ({result.total} total):", ""]
    for rec in result.recommendations:
        lines.append(f"  {rec.summary()}")
        lines.append(f"    Suggestion: {rec.suggestion}")
        lines.append("")
    return "\n".join(lines)


def _format_json(result: RecommendationResult) -> str:
    data = [
        {
            "server": r.server,
            "job": r.job_name,
            "code": r.code,
            "message": r.message,
            "suggestion": r.suggestion,
        }
        for r in result.recommendations
    ]
    return json.dumps({"total": result.total, "recommendations": data}, indent=2)


def run_recommend(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden recommend",
        description="Generate improvement recommendations for cron jobs.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", dest="fmt"
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = recommend(config)

    if args.fmt == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    return 0
