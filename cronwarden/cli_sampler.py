"""CLI entry point for the sampler command."""
from __future__ import annotations
import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.sampler import sample_config


def _format_text(result) -> str:
    return str(result)


def _format_json(result) -> str:
    data = [
        {"server": s.server, "job": s.job.name, "schedule": s.job.schedule, "command": s.job.command}
        for s in result.samples
    ]
    return json.dumps({"total": result.total, "samples": data}, indent=2)


def run_sampler(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cronwarden sample", description="Sample random cron jobs for spot-checking.")
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument("-n", "--count", type=int, default=5, help="Number of jobs to sample (default: 5)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--tag", default=None, help="Filter pool to jobs with this tag")
    parser.add_argument("--format", choices=["text", "json"], default="text", dest="fmt")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = sample_config(config, n=args.count, seed=args.seed, tag=args.tag)

    if args.fmt == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    return 0


if __name__ == "__main__":
    sys.exit(run_sampler())
