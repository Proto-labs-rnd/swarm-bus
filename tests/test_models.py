"""Unit tests for BusMessage and MessageType models."""

import json
import pytest
from swarm_bus.models import BusMessage, MessageType


class TestMessageType:
    def test_all_values(self):
        assert set(MessageType.values()) == {"ask", "inform", "alert", "ack"}

    def test_enum_from_string(self):
        assert MessageType("alert") is MessageType.ALERT

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            MessageType("unknown")


class TestBusMessage:
    def test_auto_id_generated(self):
        msg = BusMessage(from_agent="proto", to="orion", type=MessageType.INFORM, payload="hello")
        assert msg.id.startswith("proto-")
        assert len(msg.id) > 6

    def test_explicit_id_preserved(self):
        msg = BusMessage(from_agent="a", to="b", type=MessageType.ACK, payload="ok", id="custom-123")
        assert msg.id == "custom-123"

    def test_ts_auto_set(self):
        import time
        before = int(time.time()) - 1
        msg = BusMessage(from_agent="a", to="b", type=MessageType.ASK, payload="?")
        assert msg.ts >= before

    def test_to_json_roundtrip(self):
        msg = BusMessage(from_agent="proto", to="all", type=MessageType.ALERT, payload="disk full")
        data = json.loads(msg.to_json())
        assert data["from"] == "proto"
        assert data["to"] == "all"
        assert data["type"] == "alert"
        assert data["payload"] == "disk full"
        assert "id" in data
        assert "ts" in data

    def test_from_json_roundtrip(self):
        original = BusMessage(from_agent="orion", to="proto", type=MessageType.INFORM, payload="done")
        restored = BusMessage.from_json(original.to_json())
        assert restored.id == original.id
        assert restored.from_agent == "orion"
        assert restored.to == "proto"
        assert restored.type is MessageType.INFORM
        assert restored.payload == "done"

    def test_from_json_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            BusMessage.from_json("not json{{")

    def test_from_json_missing_fields(self):
        with pytest.raises(ValueError, match="missing fields"):
            BusMessage.from_json('{"id": "x", "from": "a"}')

    def test_is_for_exact_match(self):
        msg = BusMessage(from_agent="a", to="orion", type=MessageType.ASK, payload="?")
        assert msg.is_for("orion") is True
        assert msg.is_for("proto") is False

    def test_is_for_broadcast(self):
        msg = BusMessage(from_agent="a", to="all", type=MessageType.ALERT, payload="!")
        assert msg.is_for("orion") is True
        assert msg.is_for("proto") is True

    def test_type_coerced_from_string(self):
        msg = BusMessage(from_agent="a", to="b", type="ack", payload="ok")  # type: ignore[arg-type]
        assert msg.type is MessageType.ACK
