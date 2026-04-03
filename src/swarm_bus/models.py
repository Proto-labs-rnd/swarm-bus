"""Data models for swarm-bus messages."""

from __future__ import annotations

import time
import hashlib
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class MessageType(str, Enum):
    """Supported message types on the swarm bus."""
    ASK = "ask"
    INFORM = "inform"
    ALERT = "alert"
    ACK = "ack"

    @classmethod
    def values(cls) -> list[str]:
        return [e.value for e in cls]


@dataclass
class BusMessage:
    """A single message on the swarm bus."""

    from_agent: str
    to: str
    type: MessageType
    payload: str
    id: str = field(default="")
    ts: int = field(default_factory=lambda: int(time.time()))

    def __post_init__(self) -> None:
        if not self.id:
            raw = f"{self.from_agent}-{self.ts}-{self.payload}"
            self.id = f"{self.from_agent}-{hashlib.sha256(raw.encode()).hexdigest()[:8]}"
        if isinstance(self.type, str):
            self.type = MessageType(self.type)

    def to_json(self) -> str:
        """Serialize message to JSON line."""
        d = {
            "id": self.id,
            "ts": self.ts,
            "from": self.from_agent,
            "to": self.to,
            "type": self.type.value,
            "payload": self.payload,
        }
        return json.dumps(d, ensure_ascii=False)

    @classmethod
    def from_json(cls, line: str) -> "BusMessage":
        """Deserialize a JSON line from the bus file."""
        try:
            d = json.loads(line.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON message: {line!r}") from e
        required = {"id", "ts", "from", "to", "type", "payload"}
        missing = required - set(d.keys())
        if missing:
            raise ValueError(f"Message missing fields: {missing}")
        return cls(
            id=d["id"],
            ts=d["ts"],
            from_agent=d["from"],
            to=d["to"],
            type=MessageType(d["type"]),
            payload=d["payload"],
        )

    def is_for(self, agent: str) -> bool:
        """Return True if this message is addressed to `agent`."""
        return self.to == agent or self.to == "all"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BusMessage):
            return NotImplemented
        return self.id == other.id

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"BusMessage(id={self.id!r}, from={self.from_agent!r}, "
            f"to={self.to!r}, type={self.type.value!r})"
        )
