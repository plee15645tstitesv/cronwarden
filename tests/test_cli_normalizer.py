"""Tests for cronwarden.cli_normalizer."""

import json
import textwrap
import pytest
from cronwarden.cli_normalizer import run_normalize


@pytest.fixture
def config_file(tmp_path):
    cfg = tmp_path / "cronwarden.yaml"
    cfg.write_text(
        textwrap.dedent("""\
            servers:
              - name: web-01
                jobs:
                  - name: daily-backup
                    schedule: "@daily"
                    command: /usr/bin/backup.sh
                    description: Daily backup
                  - name: hourly-sync
                    schedule: "0 * * * *"
                    command: /usr/bin/sync.sh
        """)
    )
    return str(cfg)


@pytest.fixture
def canonical_config_file(tmp_path):
    cfg = tmp_path / "canonical.yaml"
    cfg.write_text(
        textwrap.dedent("""\
            servers:
              - name: web-01
                jobs:
                  - name: job1
                    schedule: "0 0 * * *"
                    command: /usr/bin/job1.sh
        """)
    )
    return str(cfg)


def _run(argv):
    return run_normalize(argv)


def test_run_normalize_exits_zero(config_file):
    assert _run([config_file]) == 0


def test_run_normalize_bad_config_exits_one(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("not: valid: cron: config\n")
    assert _run([str(bad)]) == 1


def test_run_normalize_json_output_is_valid(config_file, capsys):
    _run([config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "total" in data
    assert "jobs" in data


def test_run_normalize_json_contains_alias_change(config_file, capsys):
    _run([config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    changed = [j for j in data["jobs"] if j["was_changed"]]
    assert any(j["original_schedule"] == "@daily" for j in changed)


def test_run_normalize_text_mentions_changed(config_file, capsys):
    _run([config_file])
    out = capsys.readouterr().out
    assert "changed" in out.lower()


def test_run_normalize_changed_only_no_output_when_canonical(canonical_config_file, capsys):
    _run([canonical_config_file, "--changed-only"])
    out = capsys.readouterr().out
    assert "No schedule normalization changes detected" in out


def test_run_normalize_missing_file_exits_one():
    assert _run(["/nonexistent/path/config.yaml"]) == 1
