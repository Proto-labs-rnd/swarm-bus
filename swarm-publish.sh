#!/bin/bash
# swarm-publish.sh — Publier directement dans un topic Telegram depuis n'importe quel agent
# Usage: swarm-publish.sh <agent_name> <chat_id> <topic_id> <message>
# Exemple: swarm-publish.sh "Orion" "-1001234567" "42" "CPU spike détecté sur cortex"

AGENT_NAME=$1
CHAT_ID=$2
TOPIC_ID=$3
MESSAGE=$4

if [ -z "$AGENT_NAME" ] || [ -z "$CHAT_ID" ] || [ -z "$TOPIC_ID" ] || [ -z "$MESSAGE" ]; then
  echo "Usage: $0 <agent_name> <chat_id> <topic_id> <message>"
  exit 1
fi

# Rate limiting: max 1 publication par 30s par agent
RATE_FILE="/tmp/swarm-rate-${AGENT_NAME,,}"
if [ -f "$RATE_FILE" ]; then
  LAST=$(cat "$RATE_FILE")
  NOW=$(date +%s)
  DIFF=$((NOW - LAST))
  if [ "$DIFF" -lt 30 ]; then
    echo "[swarm-publish] Rate limited: ${AGENT_NAME} must wait $((30 - DIFF))s" >&2
    exit 2
  fi
fi
date +%s > "$RATE_FILE"

# Emoji par agent
case "${AGENT_NAME,,}" in
  orion|sre)   EMOJI="🔧" ;;
  specter|research) EMOJI="🔎" ;;
  aegis)       EMOJI="🛡️" ;;
  proto|labs)  EMOJI="🧪" ;;
  tachikoma)   EMOJI="⚡" ;;
  *)           EMOJI="🤖" ;;
esac

FORMATTED="${EMOJI} [${AGENT_NAME}] ${MESSAGE}"

openclaw message send \
  --channel telegram \
  --target "$CHAT_ID" \
  --thread-id "$TOPIC_ID" \
  --message "$FORMATTED"

echo "[swarm-publish] Published as ${AGENT_NAME}: ${FORMATTED}"
