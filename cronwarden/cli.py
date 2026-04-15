"""Command-line interface for cronwarden."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from cronwarden.auditor import audit_config, has_failures
from cronwarden.config import load_config, ConfigError
from cronwarden.formatter import render, FORMATS


@click.command()
@click.argument("config_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(list(FORMATS.keys()), case_sensitive=False),
    default="text",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--fail-fast",
    is_flag=True,
    default=False,
    help="Exit with code 1 if any job fails validation.",
)
@click.version_option(package_name="cronwarden")
def main(
    config_path: Path,
    fmt: str,
    fail_fast: bool,
) -> None:
    """Audit cron jobs defined in CONFIG_PATH."""
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        click.echo(f"Error loading config: {exc}", err=True)
        sys.exit(2)

    reports = audit_config(config)
    output = render(reports, fmt=fmt)
    click.echo(output)

    if fail_fast and has_failures(reports):
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
