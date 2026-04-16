import pytest
from cronwarden.classifier import classify_config, ClassificationResult, ClassifiedJob, CATEGORIES
from cronwarden.config import Config, Server, CronJob


def _make_job(name, command, schedule="0 * * * *", tags=None):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [])


def _make_config(jobs_by_server):
    servers = []
    for server_name, jobs in jobs_by_server.items():
        servers.append(Server(name=server_name, host=f"{server_name}.example.com", jobs=jobs))
    return Config(servers=servers)


def test_classify_config_returns_classification_result():
    config = _make_config({"web": [_make_job("backup-db", "pg_dump mydb")]})
    result = classify_config(config)
    assert isinstance(result, ClassificationResult)


def test_backup_job_classified_correctly():
    config = _make_config({"web": [_make_job("dump", "pg_dump mydb > out.sql")]})
    result = classify_config(config)
    assert len(result.classified) == 1
    assert result.classified[0].category == "backup"


def test_cleanup_job_classified_correctly():
    config = _make_config({"web": [_make_job("purge-logs", "/usr/bin/purge_old_logs.sh")]})
    result = classify_config(config)
    assert result.classified[0].category == "cleanup"


def test_unclassified_job_detected():
    config = _make_config({"web": [_make_job("mystery", "/opt/run_thing.sh")]})
    result = classify_config(config)
    assert result.has_unclassified()
    assert len(result.unclassified) == 1


def test_total_counts_all_jobs():
    config = _make_config({
        "web": [
            _make_job("backup-db", "mysqldump mydb"),
            _make_job("unknown", "/opt/mystery.sh"),
        ]
    })
    result = classify_config(config)
    assert result.total() == 2


def test_by_category_groups_correctly():
    config = _make_config({
        "web": [
            _make_job("backup1", "pg_dump db1"),
            _make_job("backup2", "rsync /data /backup"),
            _make_job("check-health", "check_service.sh"),
        ]
    })
    result = classify_config(config)
    by_cat = result.by_category()
    assert "backup" in by_cat
    assert len(by_cat["backup"]) == 2
    assert "monitoring" in by_cat


def test_classified_job_summary():
    job = _make_job("backup-db", "pg_dump mydb")
    cj = ClassifiedJob(server="prod", job=job, category="backup")
    s = cj.summary()
    assert "backup" in s
    assert "prod" in s
    assert "backup-db" in s


def test_name_based_classification():
    config = _make_config({"web": [_make_job("send-report", "/opt/run.sh")]})
    result = classify_config(config)
    assert result.classified[0].category == "reporting"


def test_multiple_servers():
    config = _make_config({
        "web": [_make_job("backup-db", "pg_dump mydb")],
        "app": [_make_job("vacuum-db", "vacuumdb")],
    })
    result = classify_config(config)
    assert result.total() == 2
    categories = {cj.category for cj in result.classified}
    assert "backup" in categories
    assert "maintenance" in categories
