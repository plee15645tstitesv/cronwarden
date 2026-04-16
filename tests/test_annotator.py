import pytest
from cronwarden.config import Config, Server, CronJob
from cronwarden.annotator import annotate_config, list_annotations, Annotation, AnnotationResult


def _make_job(name="backup", schedule="0 2 * * *", command="/usr/bin/backup", tags=None):
    return CronJob(name=name, schedule=schedule, command=command, tags=tags or [])


def _make_config():
    jobs_a = [_make_job("backup"), _make_job("cleanup", command="/usr/bin/clean")]
    jobs_b = [_make_job("sync", command="/usr/bin/sync")]
    servers = [
        Server(name="web-01", host="web-01.example.com", jobs=jobs_a),
        Server(name="db-01", host="db-01.example.com", jobs=jobs_b),
    ]
    return Config(servers=servers)


def test_annotate_config_returns_annotation_result():
    config = _make_config()
    result = annotate_config(config, {})
    assert isinstance(result, AnnotationResult)


def test_no_notes_returns_empty_result():
    config = _make_config()
    result = annotate_config(config, {})
    assert not result.has_annotations
    assert result.total == 0


def test_annotate_known_job():
    config = _make_config()
    notes = {"web-01": {"backup": "Critical nightly backup"}}
    result = annotate_config(config, notes)
    assert result.has_annotations
    assert result.total == 1


def test_annotation_fields():
    config = _make_config()
    notes = {"web-01": {"backup": "Critical nightly backup"}}
    result = annotate_config(config, notes)
    ann = result.annotations[0]
    assert ann.server == "web-01"
    assert ann.job_name == "backup"
    assert ann.note == "Critical nightly backup"


def test_unknown_server_is_skipped():
    config = _make_config()
    notes = {"ghost-server": {"backup": "note"}}
    result = annotate_config(config, notes)
    assert not result.has_annotations


def test_unknown_job_is_skipped():
    config = _make_config()
    notes = {"web-01": {"nonexistent-job": "note"}}
    result = annotate_config(config, notes)
    assert not result.has_annotations


def test_multiple_annotations():
    config = _make_config()
    notes = {
        "web-01": {"backup": "note1", "cleanup": "note2"},
        "db-01": {"sync": "note3"},
    }
    result = annotate_config(config, notes)
    assert result.total == 3


def test_for_server_filters_correctly():
    config = _make_config()
    notes = {
        "web-01": {"backup": "note1"},
        "db-01": {"sync": "note3"},
    }
    result = annotate_config(config, notes)
    web_anns = result.for_server("web-01")
    assert len(web_anns) == 1
    assert web_anns[0].job_name == "backup"


def test_for_job_returns_correct_annotation():
    config = _make_config()
    notes = {"web-01": {"backup": "important"}}
    result = annotate_config(config, notes)
    ann = result.for_job("web-01", "backup")
    assert ann is not None
    assert ann.note == "important"


def test_for_job_returns_none_when_missing():
    config = _make_config()
    result = annotate_config(config, {})
    assert result.for_job("web-01", "backup") is None


def test_list_annotations_returns_strings():
    config = _make_config()
    notes = {"web-01": {"backup": "check this"}}
    result = annotate_config(config, notes)
    lines = list_annotations(result)
    assert isinstance(lines, list)
    assert any("backup" in l for l in lines)


def test_annotation_summary_format():
    ann = Annotation(server="web-01", job_name="backup", note="test note")
    assert ann.summary() == "[web-01] backup: test note"
