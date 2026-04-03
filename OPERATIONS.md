# Operations — swarm-bus

## Purpose
`swarm-bus` provides lightweight shell utilities for asynchronous inter-agent messaging using a JSONL bus file and per-agent seen markers.

## Files
- `swarm-bus-write.sh` — append a message to the shared bus
- `swarm-bus-read.sh` — read unseen messages for one agent
- `swarm-publish.sh` — publish a formatted message to a Telegram topic through `openclaw`

## Install
### System requirements
- Bash
- `jq`
- Coreutils (`tail`, `grep`, `sha256sum`, `wc`, `mkdir`, `touch`)
- `openclaw` CLI for `swarm-publish.sh`

### Optional Python test tooling
```bash
python3 -m pip install -e .[test]
# or
python3 -m pip install -r requirements.txt
```

## Configuration
### Shared bus paths
The scripts currently use fixed paths:
- Bus file: `/mnt/shared-storage/swarm/bus.jsonl`
- Seen markers: `/mnt/shared-storage/swarm/agents/<agent>.seen`

Ensure the parent directory exists and is writable by the operators running the scripts.

### Telegram publish path
`swarm-publish.sh` requires:
- a working `openclaw` CLI installation
- access to a Telegram target chat id
- a valid topic/thread id

## Usage
### Write a bus message
```bash
./swarm-bus-write.sh proto orion alert "Chroma container is unhealthy"
```

### Read pending messages
```bash
./swarm-bus-read.sh orion
```

### Publish to Telegram
```bash
./swarm-publish.sh proto -1001234567 42 "CPU spike detected on cortex"
```

## Health checks
### Basic bus health
- `jq` is installed: `jq --version`
- bus directory is writable: `test -w /mnt/shared-storage/swarm || echo not-writable`
- bus file is growing when writes happen: `tail -n 5 /mnt/shared-storage/swarm/bus.jsonl`

### Functional smoke check
1. Write a test message:
   ```bash
   ./swarm-bus-write.sh proto proto inform "smoke-test"
   ```
2. Read it back once:
   ```bash
   ./swarm-bus-read.sh proto
   ```
3. Re-run the read command and confirm the same message is not repeated.

### Publish health
Run a low-risk test publish to a non-production thread and confirm:
- command exits successfully
- message appears with the expected agent emoji prefix
- repeated publish within 30s is rate-limited

## Troubleshooting
### `jq: command not found`
Install `jq` and retry.

### No messages returned
Possible causes:
- bus file does not exist yet
- target agent name does not match `to`
- messages were already marked in `agents/<agent>.seen`
- sender is the same as the reading agent and is intentionally filtered

### Duplicate or unexpected reads
Check whether the seen file is writable and preserved between runs.

### `swarm-publish.sh` exits with code 2
Rate limiting is active. Wait 30 seconds before retrying for the same agent.

### Telegram publish fails
Verify:
- `openclaw` is installed and on `PATH`
- chat id and topic id are valid
- the caller has permission to post in the target thread

## Operational notes
- The read script trims seen markers after 1000 entries, keeping the latest 500.
- The write script rotates the bus after 500 lines.
- Current implementation is intentionally simple and shell-first; it is suitable for lightweight coordination, not guaranteed delivery semantics.
