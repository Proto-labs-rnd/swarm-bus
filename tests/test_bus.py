"""Unit and integration tests for SwarmBus core logic."""

import json
import pytest
from pathlib import Path

from swarm_bus.bus import SwarmBus
from swarm_bus.config import SwarmBusConfig
from swarm_bus.models import BusMessage, MessageType


@pytest.fixture
def bus(tmp_path: Path) -> SwarmBus:
    cfg = SwarmBusConfig(bus_dir=tmp_path / "swarm")
    return SwarmBus(config=cfg)


class TestWrite:
    def test_write_creates_bus_file(self, bus: SwarmBus):
        bus.write("proto", "orion", MessageType.INFORM, "hello")
        assert bus.config.bus_file.exists()

    def test_write_appends_valid_jsonl(self, bus: SwarmBus):
        bus.write("proto", "orion", MessageType.INFORM, "msg1")
        bus.write("proto", "orion", MessageType.ALERT, "msg2")
        lines = bus.config.bus_file.read_text().strip().splitlines()
        assert len(lines) == 2
        for line in lines:
            json.loads(line)  # must parse without error

    def test_write_returns_bus_message(self, bus: SwarmBus):
        msg = bus.write("proto", "orion", MessageType.ACK, "done")
        assert isinstance(msg, BusMessage)
        assert msg.from_agent == "proto"
        assert msg.to == "orion"

    def test_write_empty_from_raises(self, bus: SwarmBus):
        with pytest.raises(ValueError, match="from_agent"):
            bus.write("", "orion", MessageType.INFORM, "hi")

    def test_write_empty_to_raises(self, bus: SwarmBus):
        with pytest.raises(ValueError, match="to"):
            bus.write("proto", "", MessageType.INFORM, "hi")

    def test_write_empty_payload_raises(self, bus: SwarmBus):
        with pytest.raises(ValueError, match="payload"):
            bus.write("proto", "orion", MessageType.INFORM, "   ")

    def test_write_rotation_keeps_max_lines(self, tmp_path: Path):
        cfg = SwarmBusConfig(bus_dir=tmp_path / "swarm", bus_max_lines=10)
        bus = SwarmBus(config=cfg)
        for i in range(20):
            bus.write("proto", "orion", MessageType.INFORM, f"msg {i}")
        lines = bus.config.bus_file.read_text().strip().splitlines()
        assert len(lines) <= 10


class TestRead:
    def test_read_delivers_targeted_message_once(self, bus: SwarmBus):
        bus.write("proto", "orion", MessageType.INFORM, "hello orion")
        msgs = list(bus.read("orion"))
        assert len(msgs) == 1
        assert msgs[0].payload == "hello orion"
        # Second read must return nothing
        assert list(bus.read("orion")) == []

    def test_read_delivers_broadcast(self, bus: SwarmBus):
        bus.write("proto", "all", MessageType.ALERT, "system alert")
        msgs_orion = list(bus.read("orion"))
        msgs_proto = list(bus.read("proto"))
        assert len(msgs_orion) == 1
        # proto cannot read its own message even broadcast
        assert len(msgs_proto) == 0

    def test_read_skips_own_messages(self, bus: SwarmBus):
        bus.write("orion", "all", MessageType.INFORM, "from orion")
        msgs = list(bus.read("orion"))
        assert msgs == []

    def test_read_skips_messages_for_other_agents(self, bus: SwarmBus):
        bus.write("proto", "aegis", MessageType.ASK, "secret")
        msgs = list(bus.read("orion"))
        assert msgs == []

    def test_read_multiple_messages(self, bus: SwarmBus):
        bus.write("proto", "orion", MessageType.INFORM, "one")
        bus.write("proto", "orion", MessageType.ALERT, "two")
        bus.write("proto", "aegis", MessageType.INFORM, "not for orion")
        msgs = list(bus.read("orion"))
        assert len(msgs) == 2
        payloads = {m.payload for m in msgs}
        assert payloads == {"one", "two"}

    def test_read_empty_bus_returns_nothing(self, bus: SwarmBus):
        assert list(bus.read("orion")) == []

    def test_read_marks_messages_as_seen(self, bus: SwarmBus):
        bus.write("proto", "orion", MessageType.INFORM, "seen-test")
        list(bus.read("orion"))
        seen = bus.config.seen_file("orion").read_text()
        assert len(seen.strip()) > 0

    def test_read_trims_seen_file(self, tmp_path: Path):
        cfg = SwarmBusConfig(
            bus_dir=tmp_path / "swarm",
            seen_max_entries=5,
            seen_keep_entries=3,
        )
        bus = SwarmBus(config=cfg)
        # Pre-populate the seen file with 5 fake IDs
        cfg.agents_dir.mkdir(parents=True, exist_ok=True)
        seen_file = cfg.seen_file("orion")
        seen_file.write_text("\n".join(f"fake-id-{i}" for i in range(5)) + "\n")
        # Add one more real message to trigger trim
        bus.write("proto", "orion", MessageType.INFORM, "trim me")
        list(bus.read("orion"))
        remaining = seen_file.read_text().strip().splitlines()
        assert len(remaining) <= cfg.seen_max_entries

    def test_read_tolerates_malformed_lines(self, bus: SwarmBus):
        bus.config.bus_dir.mkdir(parents=True, exist_ok=True)
        bus.config.bus_file.write_text('bad json\n{"id":"x","ts":1,"from":"a","to":"orion","type":"inform","payload":"ok"}\n')
        msgs = list(bus.read("orion"))
        # Should skip bad line and deliver the good one
        assert len(msgs) == 1
        assert msgs[0].payload == "ok"


class TestStats:
    def test_stats_empty_bus(self, bus: SwarmBus):
        stats = bus.stats()
        assert stats["bus_lines"] == 0
        assert stats["agents"] == []

    def test_stats_after_writes_and_reads(self, bus: SwarmBus):
        bus.write("proto", "orion", MessageType.INFORM, "hi")
        list(bus.read("orion"))
        stats = bus.stats()
        assert stats["bus_lines"] == 1
        assert "orion" in stats["agents"]
