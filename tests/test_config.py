"""Tests for SwarmBusConfig."""

import pytest
from pathlib import Path
from swarm_bus.config import SwarmBusConfig


def test_default_paths():
    cfg = SwarmBusConfig(bus_dir=Path("/tmp/swarm"))
    assert cfg.bus_file == Path("/tmp/swarm/bus.jsonl")
    assert cfg.agents_dir == Path("/tmp/swarm/agents")
    assert cfg.seen_file("orion") == Path("/tmp/swarm/agents/orion.seen")


def test_validation_max_lines_too_small():
    with pytest.raises(ValueError, match="bus_max_lines"):
        SwarmBusConfig(bus_dir=Path("/tmp"), bus_max_lines=5).validate()


def test_validation_tail_lines_zero():
    with pytest.raises(ValueError, match="tail_lines"):
        SwarmBusConfig(bus_dir=Path("/tmp"), tail_lines=0).validate()


def test_validation_publish_rate_limit_zero():
    with pytest.raises(ValueError, match="publish_rate_limit_seconds"):
        SwarmBusConfig(bus_dir=Path("/tmp"), publish_rate_limit_seconds=0).validate()


def test_validation_seen_max_less_than_keep():
    with pytest.raises(ValueError, match="seen_max_entries"):
        SwarmBusConfig(
            bus_dir=Path("/tmp"), seen_max_entries=100, seen_keep_entries=200
        ).validate()


def test_valid_config_passes():
    cfg = SwarmBusConfig(bus_dir=Path("/tmp/test"))
    cfg.validate()  # should not raise


def test_invalid_env_integer_raises(monkeypatch):
    monkeypatch.setenv("SWARM_BUS_MAX_LINES", "not-an-int")
    with pytest.raises(ValueError, match="SWARM_BUS_MAX_LINES"):
        SwarmBusConfig(bus_dir=Path("/tmp/test"))
