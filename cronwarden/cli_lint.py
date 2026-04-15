"""CLI subcommand: lint — check cron jobs for common issues."""

import sys
import argparse
from cronwarden.config import load_config, ConfigError
from cronwarden.linter import lint_all


def run_lint(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden lint",
        description="Lint cron jobs for common issues and best-practice violations.",
    )
    parser.add_argument("config", help="Path to cronwarden config file (YAML).")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if any warnings are found.",
    )
    parser.add_argument(
        "--server",
        metavar="NAME",
        help="Lint only jobs belonging to the named server.",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 1

    servers = config.servers
    if args.server:
        servers = [s for s in servers if s.name == args.server]
        if not servers:
            print(f"No server named '{args.server}' found in config.", file=sys.stderr)
            return 1

    total_warnings = 0
    for server in servers:
        results = lint_all(server.jobs)
        dirty = [r for r in results if not r.is_clean]
        if dirty:
            print(f"\n{server.name}:")
            for result in dirty:
                for warning in result.warnings:
                    print(f"  {warning}")
                    total_warnings += 1

    if total_warnings == 0:
        print("No lint warnings found.")
        return 0

    print(f"\n{total_warnings} warning(s) found.")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(run_lint())
