"""Integration tests: classifier works end-to-end with real config loading."""

import pytest
from cronwarden.config import load_config
from cronwarden.classifier import classify_config


@pytest.fixture
def config_file(tmp_path):
    content = """servers:
  - name: prod
    host: prod.example.com
    jobs:
      - name: nightly-backup
        schedule: "0 1 * * *"
        command: mysqldump -u root mydb > /backups/mydb.sql
        tags: [backup]
      - name: health-check
        schedule: "*/5 * * * *"
        command: check_service.sh --alert
        tags: [monitoring]
      - name: send-weekly-report
        schedule: "0 9 * * 1"
        command: /opt/reports/weekly.py --email admin@example.com
      - name: log-rotate
        schedule: "0 0 * * *"
        command: /usr/sbin/logrotate /etc/logrotate.conf
      - name: mystery-job
        schedule: "30 4 * * *"
        command: /opt/proprietary/run.sh
"""
    f = tmp_path / "cronwarden.yaml"
    f.write_text(content)
    return str(f)


def test_integration_classify_from_file(config_file):
    config = load_config(config_file)
    result = classify_config(config)
    assert result.total() == 5


def test_integration_backup_detected(config_file):
    config = load_config(config_file)
    result = classify_config(config)
    by_cat = result.by_category()
    assert "backup" in by_cat
    assert any(cj.job.name == "nightly-backup" for cj in by_cat["backup"])


def test_integration_monitoring_detected(config_file):
    config = load_config(config_file)
    result = classify_config(config)
    by_cat = result.by_category()
    assert "monitoring" in by_cat


def test_integration_unclassified_present(config_file):
    config = load_config(config_file)
    result = classify_config(config)
    assert result.has_unclassified()
    unclassified_names = [j.name for _, j in result.unclassified]
    assert "mystery-job" in unclassified_names
