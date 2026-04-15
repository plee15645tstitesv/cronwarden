"""CLI subcommand: cronwarden notify"""

import sys
import json
import argparse
from cronwarden.config import load_config, ConfigError
from cronwarden.notifier import NotificationChannel, notify


def _parse_channels(channels_arg: list) -> list:
    """Parse channel strings of the form 'webhook:http://...' into NotificationChannel objects."""
    parsed = []
    for raw in channels_arg:
        if ":" not in raw:
            raise ValueError(f"Invalid channel format '{raw}'. Expected 'type:target'.")
        ch_type, _, target = raw.partition(":")
        parsed.append(NotificationChannel(type=ch_type.strip(), target=target.strip()))
    return parsed


def run_notify(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden notify",
        description="Audit cron jobs and send notifications.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--channel",
        dest="channels",
        action="append",
        default=[],
        metavar="TYPE:TARGET",
        help="Notification channel in 'type:target' format (repeatable)",
    )
    parser.add_argument(
        "--always",
        action="store_true",
        default=False,
        help="Send notifications even when there are no failures",
    )
    parser.add_argument("--json", dest="as_json", action="store_true", default=False)

    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 1

    if not args.channels:
        print("No channels specified. Use --channel type:target.", file=sys.stderr)
        return 1

    try:
        channels = _parse_channels(args.channels)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    for ch in channels:
        if args.always:
            ch.on_failure_only = False

    results = notify(config, channels)

    if args.as_json:
        output = [
            {"channel": r.channel.type, "target": r.channel.target, "success": r.success, "message": r.message}
            for r in results
        ]
        print(json.dumps(output, indent=2))
    else:
        for r in results:
            print(str(r))

    all_ok = all(r.success for r in results)
    return 0 if all_ok else 1
