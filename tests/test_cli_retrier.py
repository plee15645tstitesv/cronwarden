import json
import pytest
from unittest.mock import patch
from cronwarden.cli_retrier import run_retry, _format_text, _format_json
from cronwarden.retrier import RetryResult, RetriedJob


@pytest.fixture
def config_file(tmp_path):
    content = """
servers:
  - name: prod
    jobs:
      - name: backup
        command: /bin/backup
        schedule: "0 2 * * *"
        tags: [backup]
      - name: cleanup
        command: /bin/clean
        schedule: "0 3 * * *"
        tags: [cleanup]
"""
    f = tmp_path / "cronwarden.yml"
    f.write_text(content)
    return str(f)


def _run(args):
    with pytest.raises(SystemExit) as exc:
        run_retry(args)
    return exc.value.code


def test_run_retry_exits_zero(config_file):
    assert _run([config_file]) == 0


def test_run_retry_bad_config_exits_one(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("not: valid: config")
    assert _run([str(bad)]) == 1


def test_run_retry_json_output_is_valid(config_file, capsys):
    _run([config_file, "--format", "json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 2


def test_run_retry_tag_filter(config_file, capsys):
    _run([config_file, "--format", "json", "--tags", "backup"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 1
    assert data[0]["job"] == "backup"


def test_run_retry_custom_policy(config_file, capsys):
    _run([config_file, "--format", "json", "--max-attempts", "5", "--backoff", "30"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert all(j["max_attempts"] == 5 for j in data)
    assert all(j["backoff_seconds"] == 30 for j in data)


def test_format_text_empty():
    result = RetryResult()
    text = _format_text(result)
    assert "No jobs matched" in text


def test_format_text_contains_job_name():
    job = RetriedJob("prod", "backup", "/bin/backup", "0 2 * * *", 3, 60, ["backup"])
    result = RetryResult(jobs=[job])
    text = _format_text(result)
    assert "backup" in text
