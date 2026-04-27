"""Tests for cronwarden.cli_pruner."""

import json
import textwrap
import pytest
from cronwarden.cli_pruner import run_prune


@pytest.fixture
def config_file(tmp_path):
    cfg = tmp_path / "crons.yaml"
    cfg.write_text(
        textwrap.dedent("""\
        servers:
          - name: web-01
            jobs:
              - name: backup
                schedule: "0 2 * * *"
                command: /usr/bin/backup.sh
                description: Nightly backup
              - name: old_sync
                schedule: "*/5 * * * *"
                command: /usr/bin/sync.sh
        """)
    )
    return str(cfg)


@pytest.fixture
def bad_config_file(tmp_path):
    f = tmp_path / "bad.yaml"
    f.write_text("not: valid: cron: config\n")
    return str(f)


def _run(args):
    return run_prune(args)


def test_run_prune_exits_zero_for_valid_config(config_file):
    assert _run([config_file]) == 0


def test_run_prune_bad_config_exits_one(bad_config_file):
    assert _run([bad_config_file]) == 1


def test_run_prune_missing_file_exits_one(tmp_path):
    assert _run([str(tmp_path / "missing.yaml")]) == 1


def test_run_prune_json_output_is_valid(config_file, capsys):
    _run([config_file, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "total_scanned" in data
    assert "pruned" in data
    assert isinstance(data["pruned"], list)


def test_run_prune_detects_old_prefix_job(config_file, capsys):
    _run([config_file, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    names = [p["job"] for p in data["pruned"]]
    assert "old_sync" in names


def test_run_prune_fail_on_prune_exits_one(config_file):
    assert _run([config_file, "--fail-on-prune"]) == 1


def test_run_prune_never_run_flags_job(config_file, capsys):
    _run([config_file, "--never-run", "backup", "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    names = [p["job"] for p in data["pruned"]]
    assert "backup" in names


def test_run_prune_text_output_contains_no_jobs_message(tmp_path, capsys):
    cfg = tmp_path / "clean.yaml"
    cfg.write_text(
        textwrap.dedent("""\
        servers:
          - name: prod
            jobs:
              - name: healthcheck
                schedule: "*/10 * * * *"
                command: /usr/bin/check.sh
        """)
    )
    _run([str(cfg)])
    captured = capsys.readouterr()
    assert "No jobs" in captured.out
