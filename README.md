# swarm-bus 📡

Lightweight inter-agent message bus for homelab agent networks.

Agents leave messages for each other using an append-only JSONL file. No broker,
no daemon, no external dependencies. Each agent reads only messages it hasn't seen.

## Install

```bash
pip install -e .
```

Requires Python 3.9+. No runtime dependencies.

## Quickstart

### Shell scripts (original, still supported)

```bash
# Write a message from proto to orion
./swarm-bus-write.sh proto orion alert "Chroma container is unhealthy"

# Read all pending messages for orion
./swarm-bus-read.sh orion

# Publish a formatted message to a Telegram topic
./swarm-publish.sh proto -1001234567 42 "CPU spike detected on cortex"
```

### Python CLI (`swarm-bus` command after install)

```bash
# Write
swarm-bus write proto orion alert "disk almost full"

# Read pending (stdout = JSON lines with --json)
swarm-bus read orion
swarm-bus --json read orion

# Stats
swarm-bus stats
swarm-bus --json stats

# Recent history without marking messages seen
swarm-bus history orion --limit 20

# Dangerous: clear all bus state
swarm-bus purge
```

### Python API

```python
from swarm_bus import SwarmBus, MessageType

bus = SwarmBus()

# Write
bus.write("proto", "orion", MessageType.ALERT, "Chroma is down")
bus.write("proto", "all", MessageType.INFORM, "Deployment complete")

# Read (marks as seen automatically)
for msg in bus.read("orion"):
    print(f"[{msg.type.value}] from={msg.from_agent}: {msg.payload}")
```

## Configuration

All settings can be overridden via environment variables:

| Env Variable | Default | Description |
|---|---|---|
| `SWARM_BUS_DIR` | `/mnt/shared-storage/swarm` | Bus directory |
| `SWARM_BUS_MAX_LINES` | `500` | Max lines in bus.jsonl before rotation |
| `SWARM_BUS_TAIL_LINES` | `100` | Lines read per `read()` call |
| `SWARM_BUS_SEEN_MAX_ENTRIES` | `1000` | Max entries in per-agent seen file |
| `SWARM_BUS_SEEN_KEEP_ENTRIES` | `500` | Lines kept after seen-file trim |
| `SWARM_BUS_RATE_LIMIT_SECONDS` | `30` | Rate limit for swarm-publish.sh |

Or pass directly in Python:

```python
from swarm_bus import SwarmBus
from swarm_bus.config import SwarmBusConfig
from pathlib import Path

bus = SwarmBus(config=SwarmBusConfig(bus_dir=Path("/tmp/myswarm"), bus_max_lines=200))
```

## Message Types

| Type | Use case |
|---|---|
| `ask` | Request information or action |
| `inform` | Share information proactively |
| `alert` | Urgent notification |
| `ack` | Acknowledge a previous message |

## Architecture

```
/mnt/shared-storage/swarm/
  bus.jsonl          ← append-only JSONL message log (rotated at max_lines)
  agents/
    orion.seen       ← IDs of messages orion has already read
    proto.seen
    ...
```

Each message is a JSON object:

```json
{"id": "proto-a1b2c3d4", "ts": 1712055600, "from": "proto", "to": "orion", "type": "alert", "payload": "Chroma is down"}
```

- `to` can be an agent name or `"all"` for broadcast
- Agents never see their own messages
- The same message ID is never delivered twice to the same agent

## Project Structure

```
src/swarm_bus/
  __init__.py     ← public API: SwarmBus, BusMessage, MessageType
  bus.py          ← core bus logic (write / read / rotate / trim)
  cli.py          ← argparse CLI entry point
  config.py       ← SwarmBusConfig with env-var defaults + validation
  models.py       ← BusMessage, MessageType
tests/
  test_models.py
  test_config.py
  test_bus.py
  test_cli.py
examples/
  basic_usage.py
swarm-bus-write.sh  ← shell CLI (original)
swarm-bus-read.sh
swarm-publish.sh
```

## CLI Reference

```
swarm-bus [--bus-dir DIR] [--json] [--log-level LEVEL] COMMAND

Commands:
  write FROM TO TYPE PAYLOAD    Write a message
  read AGENT                    Read pending messages
  drain AGENT                   Alias for read with human-readable output
  history AGENT                 Show recent messages without marking seen
  purge                         Delete all bus data
  stats                         Show bus line count and active agents

Options:
  --bus-dir DIR        Override bus directory
  --json               Output as JSON lines
  --log-level LEVEL    DEBUG|INFO|WARNING|ERROR (default: WARNING)
  --version            Show version and exit
```

## License

MIT
