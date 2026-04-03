"""Tests for v0.4.0 additions: security, history, purge, __eq__."""

import tempfile
from pathlib import Path

import pytest

from swarm_bus import SwarmBus, MessageType, BusMessage
from swarm_bus.config import SwarmBusConfig


@pytest.fixture
def tmp_bus(tmp_path):
    cfg = SwarmBusConfig(bus_dir=tmp_path, bus_max_lines=100)
    return SwarmBus(config=cfg)


# --- Agent name sanitization ---

class TestAgentNameValidation:
    @pytest.mark.parametrize("name", [
        "../etc/passwd",
        "agent/../../secret",
        "agent\x00name",
        "agent:name",
        'agent"name',
        "agent<name",
        "agent>name",
        "agent|name",
        "agent\\name",
        "agent*name",
        "agent?name",
        ".",
        "..",
    ])
    def test_reject_dangerous_names(self, tmp_bus, name):
        with pytest.raises(ValueError):
            tmp_bus.write(name, "orion", MessageType.INFORM, "test")
        with pytest.raises(ValueError):
            tmp_bus.write("orion", name, MessageType.INFORM, "test")
        with pytest.raises(ValueError):
            list(tmp_bus.read(name))

    def test_reject_empty_name(self, tmp_bus):
        with pytest.raises(ValueError):
            tmp_bus.write("", "orion", MessageType.INFORM, "test")
        with pytest.raises(ValueError):
            tmp_bus.write("  ", "orion", MessageType.INFORM, "test")

    def test_reject_leading_trailing_whitespace(self, tmp_bus):
        with pytest.raises(ValueError):
            tmp_bus.write(" proto", "orion", MessageType.INFORM, "test")

    def test_valid_names_pass(self, tmp_bus):
        for name in ("proto", "tachikoma-01", "sre_orion", "agent.v2", "agent-hidden"):
            tmp_bus.write(name, "orion", MessageType.INFORM, f"from {name}")


# --- history ---

class TestHistory:
    def test_history_returns_without_marking_seen(self, tmp_bus):
        tmp_bus.write("proto", "orion", MessageType.INFORM, "msg1")
        tmp_bus.write("proto", "orion", MessageType.ALERT, "msg2")

        history = tmp_bus.history("orion", limit=10)
        assert len(history) == 2

        # read() should still deliver them (not marked seen)
        msgs = list(tmp_bus.read("orion"))
        assert len(msgs) == 2

    def test_history_empty_bus(self, tmp_bus):
        assert tmp_bus.history("orion") == []

    def test_history_limit(self, tmp_bus):
        for i in range(10):
            tmp_bus.write("proto", "orion", MessageType.INFORM, f"msg{i}")
        assert len(tmp_bus.history("orion", limit=3)) == 3

    def test_history_skips_self_and_unrelated(self, tmp_bus):
        tmp_bus.write("orion", "proto", MessageType.INFORM, "self-msg")
        tmp_bus.write("proto", "specter", MessageType.INFORM, "not-for-orion")
        assert len(tmp_bus.history("orion")) == 0


# --- purge ---

class TestPurge:
    def test_purge_removes_bus_and_seen(self, tmp_bus):
        tmp_bus.write("proto", "orion", MessageType.INFORM, "msg")
        list(tmp_bus.read("orion"))
        assert tmp_bus.config.bus_file.exists()

        tmp_bus.purge()
        assert not tmp_bus.config.bus_file.exists()
        assert not tmp_bus.config.seen_file("orion").exists()

    def test_purge_empty_bus(self, tmp_bus):
        tmp_bus.purge()  # should not raise


# --- BusMessage.__eq__ ---

class TestBusMessageEq:
    def test_same_id_equal(self):
        m1 = BusMessage(from_agent="a", to="b", type=MessageType.INFORM, payload="x", id="same")
        m2 = BusMessage(from_agent="c", to="d", type=MessageType.ALERT, payload="y", id="same")
        assert m1 == m2

    def test_different_id_not_equal(self):
        m1 = BusMessage(from_agent="a", to="b", type=MessageType.INFORM, payload="x")
        m2 = BusMessage(from_agent="a", to="b", type=MessageType.INFORM, payload="y")
        assert m1 != m2

    def test_not_equal_to_other_type(self):
        m = BusMessage(from_agent="a", to="b", type=MessageType.INFORM, payload="x")
        assert m != "not a message"
