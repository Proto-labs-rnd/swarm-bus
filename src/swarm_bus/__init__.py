"""swarm-bus — Lightweight inter-agent message bus for homelab agent networks."""

from swarm_bus.bus import SwarmBus
from swarm_bus.models import BusMessage, MessageType

__version__ = "0.5.0"
__all__ = ["SwarmBus", "BusMessage", "MessageType"]
