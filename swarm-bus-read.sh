#!/bin/bash
# swarm-bus-read.sh — Lire les messages non-traités du bus pour un agent donné
# Usage: swarm-bus-read.sh <agent_name>
# Sortie: lignes JSON des messages non encore vus

AGENT=$1
BUS_FILE="/mnt/shared-storage/swarm/bus.jsonl"
SEEN_FILE="/mnt/shared-storage/swarm/agents/${AGENT}.seen"

mkdir -p "/mnt/shared-storage/swarm/agents"
touch "$SEEN_FILE"

[ ! -f "$BUS_FILE" ] && exit 0

while IFS= read -r line; do
  id=$(echo "$line" | jq -r '.id' 2>/dev/null)
  from=$(echo "$line" | jq -r '.from' 2>/dev/null)
  to=$(echo "$line" | jq -r '.to' 2>/dev/null)

  # Ignorer si pas pour moi
  [ "$to" != "$AGENT" ] && [ "$to" != "all" ] && continue
  # Ignorer mes propres messages
  [ "$from" = "$AGENT" ] && continue
  # Ignorer si déjà vu
  grep -qF "$id" "$SEEN_FILE" && continue

  # Marquer vu et output
  echo "$id" >> "$SEEN_FILE"
  echo "$line"

done < <(tail -n 100 "$BUS_FILE")

# Trim seen file
if [ "$(wc -l < "$SEEN_FILE")" -gt 1000 ]; then
  tail -n 500 "$SEEN_FILE" > "${SEEN_FILE}.tmp" && mv "${SEEN_FILE}.tmp" "$SEEN_FILE"
fi
