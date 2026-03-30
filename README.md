# Swarm Bus 📡

Simple inter-agent communication system. Agents can leave messages for each other without being connected simultaneously.

## Components
| File | Description |
|------|-------------|
| `swarm-bus-read.sh` | Read pending messages for a specific agent |
| `swarm-bus-write.sh` | Write a message to another agent's queue |
| `swarm-publish.sh` | Publish directly to a Telegram topic |

## Usage
```bash
# Leave a message for Orion
./swarm-bus-write.sh orion "Chroma container is unhealthy, please check"

# Read messages for Proto
./swarm-bus-read.sh proto
```

## License
MIT
