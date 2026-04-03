"""Core SwarmBus implementation — Python API for the inter-agent message bus."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterator, List, Optional

from swarm_bus.config import SwarmBusConfig
from swarm_bus.models import BusMessage, MessageType

logger = logging.getLogger(__name__)


class SwarmBus:
    """Lightweight JSONL-based inter-agent message bus.

    Agents write messages to a shared bus file and read only messages
    addressed to them that they have not already seen.

    Thread safety: not guaranteed. For multi-process use, rely on the
    append-only JSONL format (atomic appends on most Linux filesystems).

    Example::

        bus = SwarmBus()
        bus.write("proto", "orion", MessageType.ALERT, "Chroma is down")
        for msg in bus.read("orion"):
            print(msg.payload)
    """

    # Characters that are never allowed in agent names
    _INVALID_CHARS = set('/\\:*?"<>|\0')

    def __init__(self, config: Optional[SwarmBusConfig] = None) -> None:
        self.config = config or SwarmBusConfig()
        self.config.validate()

    @classmethod
    def _validate_agent_name(cls, name: str, field: str = "agent") -> None:
        """Reject agent names that could cause path traversal or FS issues."""
        if not name or not name.strip():
            raise ValueError(f"{field} must not be empty")
        if name.strip() != name:
            raise ValueError(f"{field} must not have leading/trailing whitespace: {name!r}")
        if name == '.' or name == '..':
            raise ValueError(f"{field} must not be '.' or '..': {name!r}")
        bad = cls._INVALID_CHARS & set(name)
        if bad:
            raise ValueError(f"{field} contains invalid characters {bad!r}: {name!r}")

    def _ensure_dirs(self) -> None:
        """Create bus and agents directories if they don't exist."""
        self.config.bus_dir.mkdir(parents=True, exist_ok=True)
        self.config.agents_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write(
        self,
        from_agent: str,
        to: str,
        type: MessageType,
        payload: str,
    ) -> BusMessage:
        """Append a message to the bus.

        Args:
            from_agent: Sender agent name.
            to: Recipient agent name or "all" for broadcast.
            type: Message type (ask / inform / alert / ack).
            payload: Message content (plain text).

        Returns:
            The written BusMessage.

        Raises:
            ValueError: If required arguments are empty or type is invalid.
        """
        self._validate_agent_name(from_agent, "from_agent")
        self._validate_agent_name(to, "to")
        if not payload.strip():
            raise ValueError("payload must not be empty")

        msg = BusMessage(from_agent=from_agent, to=to, type=type, payload=payload)

        self._ensure_dirs()
        with self.config.bus_file.open("a", encoding="utf-8") as fh:
            fh.write(msg.to_json() + "\n")

        self._rotate_bus()
        logger.info("[bus] Written: %s", msg)
        return msg

    def _rotate_bus(self) -> None:
        """Keep the bus file below max_lines by removing oldest entries."""
        bus_file = self.config.bus_file
        if not bus_file.exists():
            return
        lines = bus_file.read_text(encoding="utf-8").splitlines()
        if len(lines) > self.config.bus_max_lines:
            trimmed = lines[-self.config.bus_max_lines :]
            self._atomic_write(bus_file, "\n".join(trimmed) + "\n")
            logger.debug("[bus] Rotated bus to %d lines", len(trimmed))

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(self, agent: str) -> Iterator[BusMessage]:
        """Yield unseen messages addressed to `agent`.

        Messages from `agent` itself are skipped (no self-delivery).
        Each yielded message is immediately marked as seen so subsequent
        calls do not return it again.

        Args:
            agent: The consuming agent's name.

        Yields:
            BusMessage objects not yet seen by this agent.
        """
        self._validate_agent_name(agent, "agent")
        bus_file = self.config.bus_file
        if not bus_file.exists():
            return

        self._ensure_dirs()
        seen_file = self.config.seen_file(agent)
        seen_file.touch(exist_ok=True)

        seen_ids = set(seen_file.read_text(encoding="utf-8").splitlines())
        lines = bus_file.read_text(encoding="utf-8").splitlines()
        tail = lines[-self.config.tail_lines :]

        new_seen: list[str] = []
        for line in tail:
            if not line.strip():
                continue
            try:
                msg = BusMessage.from_json(line)
            except ValueError as exc:
                logger.warning("[bus] Skipping malformed line: %s", exc)
                continue

            if not msg.is_for(agent):
                continue
            if msg.from_agent == agent:
                continue
            if msg.id in seen_ids:
                continue

            seen_ids.add(msg.id)
            new_seen.append(msg.id)
            logger.debug("[bus] Delivering %s → %s", msg.id, agent)
            yield msg

        if new_seen:
            with seen_file.open("a", encoding="utf-8") as fh:
                fh.write("\n".join(new_seen) + "\n")
            self._trim_seen(seen_file)

    def _trim_seen(self, seen_file: Path) -> None:
        lines = seen_file.read_text(encoding="utf-8").splitlines()
        if len(lines) > self.config.seen_max_entries:
            trimmed = lines[-self.config.seen_keep_entries :]
            self._atomic_write(seen_file, "\n".join(trimmed) + "\n")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        """Write `content` to `path` atomically (write→rename)."""
        tmp_fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
                fh.write(content)
            shutil.move(tmp_path, path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def history(self, agent: str, limit: int = 50) -> list[BusMessage]:
        """Return recent messages for *agent* WITHOUT marking them as seen.

        Useful for inspection, dashboards, or replay.
        """
        self._validate_agent_name(agent, "agent")
        bus_file = self.config.bus_file
        if not bus_file.exists():
            return []
        lines = bus_file.read_text(encoding="utf-8").splitlines()
        results: list[BusMessage] = []
        for line in reversed(lines[-self.config.tail_lines:]):
            if not line.strip():
                continue
            try:
                msg = BusMessage.from_json(line)
            except ValueError:
                continue
            if msg.is_for(agent) and msg.from_agent != agent:
                results.append(msg)
                if len(results) >= limit:
                    break
        results.reverse()
        return results

    def purge(self) -> None:
        """Delete bus file and all seen files. Use with caution."""
        bus_file = self.config.bus_file
        if bus_file.exists():
            bus_file.unlink()
        if self.config.agents_dir.exists():
            for f in self.config.agents_dir.glob("*.seen"):
                f.unlink()
        logger.info("[bus] Purged all bus state")

    def stats(self) -> dict:
        """Return basic statistics about the bus."""
        bus_file = self.config.bus_file
        if not bus_file.exists():
            return {"bus_lines": 0, "agents": []}
        lines = [l for l in bus_file.read_text(encoding="utf-8").splitlines() if l.strip()]
        agents = []
        if self.config.agents_dir.exists():
            agents = [p.stem for p in self.config.agents_dir.glob("*.seen")]
        return {"bus_lines": len(lines), "agents": agents}
