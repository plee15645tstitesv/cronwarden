import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.labeler import label_config, LabelResult


def _format_text(result: LabelResult) -> str:
    lines = []
    by_label = result.by_label()
    if not by_label:
        lines.append("No labels assigned.")
        return "\n".join(lines)
    for label, jobs in sorted(by_label.items()):
        lines.append(f"[{label}]")
        for lj in jobs:
            lines.append(f"  {lj.summary()}")
    return "\n".join(lines)


def _format_json(result: LabelResult) -> str:
    data = [
        {
            "server": lj.server,
            "job": lj.job.name,
            "labels": lj.labels,
        }
        for lj in result.labeled
    ]
    return json.dumps(data, indent=2)


def run_label(argv=None):
    parser = argparse.ArgumentParser(prog="cronwarden label", description="Label cron jobs by inferred characteristics.")
    parser.add_argument("config", help="Path to config file")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    result = label_config(config)

    if args.format == "json":
        print(_format_json(result))
    else:
        print(_format_text(result))

    sys.exit(0)
