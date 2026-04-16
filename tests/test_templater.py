import pytest
from cronwarden.templater import (
    generate_template,
    list_templates,
    TemplateResult,
    COMMON_TEMPLATES,
)


def test_list_templates_returns_all_keys():
    result = list_templates()
    assert set(result) == set(COMMON_TEMPLATES.keys())


def test_generate_template_returns_template_result():
    result = generate_template("hourly", "my-job", "/usr/bin/sync", "web-01")
    assert isinstance(result, TemplateResult)


def test_generate_template_sets_correct_schedule():
    result = generate_template("daily-midnight", "backup", "/bin/backup.sh", "db-01")
    assert result.schedule == "0 0 * * *"


def test_generate_template_sets_job_name():
    result = generate_template("hourly", "cache-clear", "/bin/clear.sh", "web-01")
    assert result.name == "cache-clear"


def test_generate_template_sets_command():
    result = generate_template("weekly-sunday", "report", "/bin/report.py", "app-01")
    assert result.command == "/bin/report.py"


def test_generate_template_sets_server():
    result = generate_template("monthly-first", "cleanup", "/bin/clean", "storage-01")
    assert result.server == "storage-01"


def test_generate_template_with_tags():
    result = generate_template("hourly", "job", "/bin/job", "srv", tags=["infra", "sync"])
    assert result.tags == ["infra", "sync"]


def test_generate_template_no_tags_defaults_empty():
    result = generate_template("hourly", "job", "/bin/job", "srv")
    assert result.tags == []


def test_generate_template_unknown_raises_value_error():
    with pytest.raises(ValueError, match="Unknown template"):
        generate_template("nonexistent", "job", "/bin/job", "srv")


def test_to_dict_contains_required_keys():
    result = generate_template("hourly", "job", "/bin/job", "srv")
    d = result.to_dict()
    assert "name" in d and "schedule" in d and "command" in d and "description" in d


def test_to_yaml_block_contains_schedule():
    result = generate_template("every-5-minutes", "poller", "/bin/poll", "srv")
    yaml_block = result.to_yaml_block()
    assert "*/5 * * * *" in yaml_block


def test_to_yaml_block_contains_tags_when_present():
    result = generate_template("weekdays-9am", "standup", "/bin/standup", "srv", tags=["ops"])
    yaml_block = result.to_yaml_block()
    assert "ops" in yaml_block


def test_to_yaml_block_no_tags_section_when_empty():
    result = generate_template("hourly", "job", "/bin/job", "srv")
    yaml_block = result.to_yaml_block()
    assert "tags:" not in yaml_block
