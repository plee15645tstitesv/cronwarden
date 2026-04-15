"""CLI subcommand for diffing two cronwarden config files."""

import sys
import json
from cronwarden.config import load_config
from cronwarden.differ import diff_configs


def run_diff(old_path: str, new_path: str, output_format: str = "text") -> int:
    """Compare two config files and print differences. Returns exit code."""
    try:
        old_config = load_config(old_path)
        new_config = load_config(new_path)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        return 2

    result = diff_configs(old_config, new_config)

    if not result.has_changes:
        if output_format == "json":
            print(json.dumps({"changes": []}))
        else:
            print("No changes detected.")
        return 0

    if output_format == "json":
        changes = []
        for d in result.diffs:
            changes.append({
                "server": d.server,
                "job": d.job_name,
                "kind": d.kind,
                "old": d.old_value,
                "new": d.new_value,
            })
        print(json.dumps({"changes": changes}, indent=2))
    elif output_format == "markdown":
        print("## Cron Job Diff\n")
        for section, items in [("Added", result.added()), ("Removed", result.removed()), ("Changed", result.changed())]:
            if items:
                print(f"### {section}\n")
                for d in items:
                    print(f"- `{d.server}/{d.job_name}`")
                    if d.kind == "changed":
                        old = d.old_value or {}
                        new = d.new_value or {}
                        for key in set(list(old.keys()) + list(new.keys())):
                            if old.get(key) != new.get(key):
                                print(f"  - {key}: `{old.get(key)}` → `{new.get(key)}`")
                print()
    else:
        print(f"Found {len(result.diffs)} change(s):\n")
        for d in result.diffs:
            print(" ", d.summary())

    return 1 if result.has_changes else 0
