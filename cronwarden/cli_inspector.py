"""CLI entry point for the `cronwarden inspect` sub-command."""

import json
import sys
from argparse import ArgumentParser, Namespace

from cronwarden.config import load_config, ConfigError
from cronwarden.inspector import inspect_job, InspectionResult


def _format_text(result: InspectionResult) -> str:
    lines = [
        f"Job       : {result.job_name}",
        f"Server    : {result.server_name}",
        f"Schedule  : {result.schedule}",
        f"Explained : {result.schedule_explanation}",
        f"Command   : {result.command}",
        f"Category  : {result.category}",
        f"Valid     : {'yes' if result.is_valid else 'no'}",
        f"Score     : {result.score} ({result.grade})",
    ]
    if result.description:
        lines.append(f"Desc      : {result.description}")
    if result.tags:
        lines.append(f"Tags      : {', '.join(result.tags)}")
    if result.validation_errors:
        lines.append("Errors    :")
        for e in result.validation_errors:
            lines.append(f"  - {e}")
    if result.lint_warnings:
        lines.append("Warnings  :")
        for w in result.lint_warnings:
            lines.append(f"  - {w}")
    return "\n".join(lines)


def _format_json(result: InspectionResult) -> str:
    return json.dumps(result.__dict__, indent=2)


def run_inspect(args: Namespace) -> int:
    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    for server in config.servers:
        for job in server.jobs:
            if job.name == args.job and server.name == args.server:
                result = inspect_job(server, job)
                if args.format == "json":
                    print(_format_json(result))
                else:
                    print(_format_text(result))
                return 0 if result.is_valid else 2

    print(f"Error: job '{args.job}' not found on server '{args.server}'", file=sys.stderr)
    return 1


def build_parser(sub) -> None:  # pragma: no cover
    p: ArgumentParser = sub.add_parser("inspect", help="Deep-inspect a single cron job")
    p.add_argument("--config", required=True)
    p.add_argument("--server", required=True)
    p.add_argument("--job", required=True)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=run_inspect)
