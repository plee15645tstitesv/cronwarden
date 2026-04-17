"""Tests for cronwarden.sampler."""
import pytest
from cronwarden.sampler import sample_config, SampleResult, SampledJob
from cronwarden.config import Config, Server, CronJob


def _make_job(name: str, tags=None) -> CronJob:
    return CronJob(name=name, schedule="0 * * * *", command=f"run_{name}", tags=tags)


def _make_config(n_servers: int = 2, jobs_per_server: int = 4) -> Config:
    servers = []
    for i in range(n_servers):
        jobs = [_make_job(f"job_{i}_{j}", tags=["backup"] if j == 0 else None) for j in range(jobs_per_server)]
        servers.append(Server(name=f"server_{i}", host=f"host_{i}", jobs=jobs))
    return Config(servers=servers)


def test_sample_config_returns_sample_result():
    config = _make_config()
    result = sample_config(config, n=3, seed=42)
    assert isinstance(result, SampleResult)


def test_sample_count_respected():
    config = _make_config(n_servers=2, jobs_per_server=4)
    result = sample_config(config, n=3, seed=1)
    assert result.total == 3


def test_sample_does_not_exceed_pool():
    config = _make_config(n_servers=1, jobs_per_server=2)
    result = sample_config(config, n=100, seed=0)
    assert result.total == 2


def test_sample_is_reproducible_with_seed():
    config = _make_config()
    r1 = sample_config(config, n=3, seed=7)
    r2 = sample_config(config, n=3, seed=7)
    assert [s.job.name for s in r1.samples] == [s.job.name for s in r2.samples]


def test_sample_differs_with_different_seed():
    config = _make_config(n_servers=3, jobs_per_server=5)
    r1 = sample_config(config, n=5, seed=1)
    r2 = sample_config(config, n=5, seed=99)
    # Very likely to differ with 15 jobs pool
    assert [s.job.name for s in r1.samples] != [s.job.name for s in r2.samples]


def test_sample_filter_by_tag():
    config = _make_config(n_servers=2, jobs_per_server=4)
    result = sample_config(config, n=10, seed=0, tag="backup")
    assert result.total == 2
    for s in result.samples:
        assert s.job.tags and "backup" in s.job.tags


def test_sample_empty_when_tag_not_found():
    config = _make_config()
    result = sample_config(config, n=5, seed=0, tag="nonexistent")
    assert result.is_empty


def test_sampled_job_summary():
    job = _make_job("myjob")
    s = SampledJob(server="prod", job=job)
    assert "prod" in s.summary()
    assert "myjob" in s.summary()


def test_sample_result_str_non_empty():
    config = _make_config()
    result = sample_config(config, n=2, seed=3)
    text = str(result)
    assert "Sampled" in text


def test_sample_result_str_empty():
    config = _make_config()
    result = sample_config(config, n=0, seed=0)
    assert "No jobs sampled" in str(result)
