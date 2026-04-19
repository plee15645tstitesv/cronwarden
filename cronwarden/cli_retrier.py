import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.retrier import RetryPolicy, apply_retry_policy


def _format_text(result) -> str:
    if not result.has_retries():
        return "No jobs matched for retry policy application.\n"
    lines = [f"Retry policy applied to {result.total()} job(s):\n"]
    for job in result.jobs:
        lines.append(f"  {job.summary()}")
    return "\n".join(lines) + "\n"


def _format_json(result) -> str:
    data = [
        {
            "server": j.server,
            "job": j.job_name,
            "command": j.command,
            "schedule": j.schedule,
            "max_attempts": j.max_attempts,
            "backoff_seconds": j.backoff_seconds,
            "tags": j.tags,
        }
        for j in result.jobs
    ]
    return json.dumps(data, indent=2)


def run_retry(argv=None):
    parser = argparse.ArgumentParser(description="Apply retry policies to cron jobs")
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--backoff", type=int, default=60)
    parser.add_argument("--tags", nargs="+", help="Filter by tags")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    policy = RetryPolicy(max_attempts=args.max_attempts, backoff_seconds=args.backoff)
    result = apply_retry_policy(config, policy=policy, tags=args.tags)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    sys.exit(0)
