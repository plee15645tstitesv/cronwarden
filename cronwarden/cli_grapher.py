"""CLI entry point for the `cronwarden graph` sub-command."""
import argparse
import json
import sys
from cronwarden.config import load_config, ConfigError
from cronwarden.grapher import build_graph, GraphResult


def _format_text(result: GraphResult, mode: str) -> str:
    lines = [f"Graph mode: {mode}", f"Nodes: {result.total_nodes}  Edges: {result.total_edges}", ""]
    if not result.has_edges:
        lines.append("  (no relationships found)")
    else:
        for edge in result.edges:
            lines.append(f"  {edge.summary()}")
    return "\n".join(lines)


def _format_json(result: GraphResult, mode: str) -> str:
    data = {
        "mode": mode,
        "total_nodes": result.total_nodes,
        "total_edges": result.total_edges,
        "nodes": result.nodes,
        "edges": [
            {"source": e.source, "target": e.target, "reason": e.reason}
            for e in result.edges
        ],
    }
    return json.dumps(data, indent=2)


def run_graph(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="cronwarden graph",
        description="Visualise relationships between cron jobs.",
    )
    parser.add_argument("config", help="Path to cronwarden config file")
    parser.add_argument(
        "--mode",
        choices=["command", "timing"],
        default="command",
        help="Relationship mode: 'command' (shared tokens) or 'timing' (same minute)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
    )
    parser.add_argument(
        "--fail-on-edges",
        action="store_true",
        help="Exit with code 1 if any edges (relationships) are found",
    )
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (ConfigError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = build_graph(config, mode=args.mode)

    if args.fmt == "json":
        print(_format_json(result, args.mode))
    else:
        print(_format_text(result, args.mode))

    if args.fail_on_edges and result.has_edges:
        return 1
    return 0
