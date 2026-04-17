"""CLI entry point for the merge command."""
import argparse
import json
import sys
from cronwarden.config import load_config
from cronwarden.merger import merge_configs


def _format_text(result) -> str:
    lines = []
    lines.append(f"Merged {result.total_servers} server(s), {result.total_jobs} job(s).")
    if result.has_conflicts:
        lines.append(f"\n{len(result.conflicts)} conflict(s) detected:")
        for c in result.conflicts:
            lines.append(f"  ! {c.summary()}")
    else:
        lines.append("No conflicts detected.")
    return "\n".join(lines)


def _format_json(result) -> str:
    data = {
        "total_servers": result.total_servers,
        "total_jobs": result.total_jobs,
        "has_conflicts": result.has_conflicts,
        "conflicts": [c.summary() for c in result.conflicts],
        "servers": [
            {
                "name": s.name,
                "host": s.host,
                "jobs": [j.name for j in s.jobs],
            }
            for s in result.merged.servers
        ],
    }
    return json.dumps(data, indent=2)


def run_merge(argv=None):
    parser = argparse.ArgumentParser(description="Merge multiple cronwarden config files")
    parser.add_argument("configs", nargs="+", help="Config files to merge")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--fail-on-conflicts", action="store_true")
    args = parser.parse_args(argv)

    configs = []
    for path in args.configs:
        try:
            configs.append(load_config(path))
        except Exception as e:
            print(f"Error loading {path}: {e}", file=sys.stderr)
            sys.exit(1)

    result = merge_configs(configs)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    if args.fail_on_conflicts and result.has_conflicts:
        sys.exit(1)
    sys.exit(0)
