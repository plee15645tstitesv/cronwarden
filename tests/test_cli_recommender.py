import json
import pytest
from cronwarden.cli_recommender import run_recommend


@pytest.fixture
def config_file(tmp_path):
    content = """
servers:
  - name: web-01
    jobs:
      - name: nightly-backup
        schedule: "0 2 * * *"
        command: /usr/bin/backup.sh
        description: Runs nightly backup
        tags: [backup]
"""
    p = tmp_path / "cronwarden.yml"
    p.write_text(content)
    return str(p)


@pytest.fixture
def noisy_config_file(tmp_path):
    content = """
servers:
  - name: web-01
    jobs:
      - name: every-minute
        schedule: "* * * * *"
        command: sudo /usr/bin/check.sh
"""
    p = tmp_path / "noisy.yml"
    p.write_text(content)
    return str(p)


def _run(argv):
    return run_recommend(argv)


def test_run_recommend_exits_zero_for_valid_config(config_file):
    assert _run([config_file]) == 0


def test_run_recommend_exits_one_for_bad_config(tmp_path):
    bad = tmp_path / "bad.yml"
    bad.write_text("not: valid: yaml: [")
    assert _run([str(bad)]) == 1


def test_run_recommend_exits_one_for_missing_file():
    assert _run(["/nonexistent/path.yml"]) == 1


def test_run_recommend_json_output_is_valid(config_file, capsys):
    _run([config_file, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "recommendations" in data
    assert "total" in data


def test_run_recommend_text_output_for_clean_config(config_file, capsys):
    _run([config_file])
    captured = capsys.readouterr()
    assert "No recommendations" in captured.out


def test_run_recommend_text_shows_issues(noisy_config_file, capsys):
    _run([noisy_config_file])
    captured = capsys.readouterr()
    assert "R001" in captured.out or "R002" in captured.out


def test_run_recommend_json_total_matches_issues(noisy_config_file, capsys):
    _run([noisy_config_file, "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["total"] == len(data["recommendations"])
