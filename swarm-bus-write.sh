#!/bin/bash
# swarm-bus-write.sh — Écrire un message sur le bus inter-agents
# Usage: swarm-bus-write.sh <from> <to> <type> <payload>
# Types: ask | inform | alert | ack
# to: agent name ou "all"

FROM=$1
TO=$2
TYPE=$3
PAYLOAD=$4

BUS_DIR="/mnt/shared-storage/swarm"
BUS_FILE="$BUS_DIR/bus.jsonl"

mkdir -p "$BUS_DIR/agents"

ID="${FROM}-$(date +%s%N | sha256sum | head -c 8)"
TS=$(date +%s)

MSG=$(jq -nc \
  --arg id "$ID" \
  --argjson ts "$TS" \
  --arg from "$FROM" \
  --arg to "$TO" \
  --arg type "$TYPE" \
  --arg payload "$PAYLOAD" \
  '{id: $id, ts: $ts, from: $from, to: $to, type: $type, payload: $payload}')

echo "$MSG" >> "$BUS_FILE"

# Rotation: garder les 500 dernières lignes
if [ "$(wc -l < "$BUS_FILE")" -gt 500 ]; then
  tail -n 500 "$BUS_FILE" > "${BUS_FILE}.tmp" && mv "${BUS_FILE}.tmp" "$BUS_FILE"
fi

echo "[bus] Written: $MSG"
