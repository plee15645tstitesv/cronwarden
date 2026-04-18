import pytest
from cronwarden.labeler import label_config, LabelResult, LabeledJob
from cronwarden.config import CronJob, Server, Config


def _make_job(name="job", schedule="0 2 * * *", command="/usr/bin/backup", description=None, tags=None):
    return CronJob(name=name, schedule=schedule, command=command, description=description, tags=tags or [])


def _make_config(servers=None):
    if servers is None:
        servers = [Server(name="web", jobs=[_make_job()])]
    return Config(servers=servers)


def test_label_config_returns_label_result():
    config = _make_config()
    result = label_config(config)
    assert isinstance(result, LabelResult)


def test_label_result_total():
    config = _make_config(servers=[
        Server(name="web", jobs=[_make_job("a"), _make_job("b")])
    ])
    result = label_config(config)
    assert result.total() == 2


def test_frequent_label_for_star_schedule():
    job = _make_job(schedule="* * * * *")
    config = _make_config(servers=[Server(name="s", jobs=[job])])
    result = label_config(config)
    labels = result.labeled[0].labels
    assert "frequent" in labels


def test_sudo_label_detected():
    job = _make_job(command="sudo /usr/bin/clean")
    config = _make_config(servers=[Server(name="s", jobs=[job])])
    result = label_config(config)
    assert "uses-sudo" in result.labeled[0].labels


def test_undocumented_label_when_no_description():
    job = _make_job(description=None)
    config = _make_config(servers=[Server(name="s", jobs=[job])])
    result = label_config(config)
    assert "undocumented" in result.labeled[0].labels


def test_no_undocumented_label_when_description_present():
    job = _make_job(description="Does something")
    config = _make_config(servers=[Server(name="s", jobs=[job])])
    result = label_config(config)
    assert "undocumented" not in result.labeled[0].labels


def test_long_running_label_for_rsync():
    job = _make_job(command="rsync -av /src /dst")
    config = _make_config(servers=[Server(name="s", jobs=[job])])
    result = label_config(config)
    assert "long-running" in result.labeled[0].labels


def test_tagged_label_when_tags_present():
    job = _make_job(tags=["backup"])
    config = _make_config(servers=[Server(name="s", jobs=[job])])
    result = label_config(config)
    assert "tagged" in result.labeled[0].labels


def test_by_label_groups_correctly():
    j1 = _make_job("a", command="sudo rm -rf /tmp")
    j2 = _make_job("b", command="sudo apt update")
    config = _make_config(servers=[Server(name="s", jobs=[j1, j2])])
    result = label_config(config)
    by_label = result.by_label()
    assert "uses-sudo" in by_label
    assert len(by_label["uses-sudo"]) == 2


def test_has_labels_false_when_all_clean():
    result = LabelResult(labeled=[])
    assert not result.has_labels()
