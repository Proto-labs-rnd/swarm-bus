#!/usr/bin/env python3
"""swarm-bus basic usage walkthrough.

Run with:  python3 examples/basic_usage.py

This demo creates a temporary bus directory and demonstrates:
1. Writing messages between agents
2. Reading pending messages (marks as seen)
3. Re-reading (no duplicates)
4. Broadcasting to all agents
5. Bus statistics
6. History (re-read without marking seen)
"""

import tempfile
import shutil
from pathlib import Path

from swarm_bus import SwarmBus, MessageType
from swarm_bus.config import SwarmBusConfig


def main() -> None:
    # Use a temporary directory so we don't pollute the real bus
    tmp = Path(tempfile.mkdtemp(prefix="swarm-demo-"))
    config = SwarmBusConfig(bus_dir=tmp, bus_max_lines=50)
    bus = SwarmBus(config=config)

    print(f"=== swarm-bus demo (bus_dir={tmp}) ===\n")

    # 1. Write messages
    print("--- Writing messages ---")
    m1 = bus.write("proto", "orion", MessageType.INFORM, "Experiment #42 completed successfully")
    m2 = bus.write("proto", "orion", MessageType.ASK, "Can you check Docker health?")
    m3 = bus.write("tachikoma", "orion", MessageType.ALERT, "CPU usage above 90%")
    print(f"  Wrote 3 messages (ids: {m1.id}, {m2.id}, {m3.id})")

    # 2. Read pending messages for orion
    print("\n--- Reading pending for 'orion' ---")
    for msg in bus.read("orion"):
        print(f"  [{msg.type.value.upper()}] from={msg.from_agent}: {msg.payload}")

    # 3. Re-read — should be empty (messages marked as seen)
    print("\n--- Re-reading for 'orion' (expect 0) ---")
    count = sum(1 for _ in bus.read("orion"))
    print(f"  Pending: {count}")

    # 4. Broadcast
    print("\n--- Broadcasting to all ---")
    bus.write("tachikoma", "all", MessageType.INFORM, "Scheduled maintenance in 10min")
    for agent in ("orion", "specter"):
        msgs = list(bus.read(agent))
        print(f"  {agent} got {len(msgs)} broadcast(s)")

    # 5. Stats
    print("\n--- Bus stats ---")
    stats = bus.stats()
    print(f"  bus_lines={stats['bus_lines']}, agents={stats['agents']}")

    # 6. History
    print("\n--- History for 'orion' (last 10, no mark) ---")
    for msg in bus.history("orion", limit=10):
        print(f"  [{msg.type.value.upper()}] from={msg.from_agent}: {msg.payload}")

    # Cleanup
    shutil.rmtree(tmp)
    print("\n=== demo complete, temp dir cleaned up ===")


if __name__ == "__main__":
    main()
