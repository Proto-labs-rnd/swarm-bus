"""Configuration for swarm-bus — loaded from env vars or config file."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_int(name: str, default: str) -> int:
    """Parse an integer environment variable with a clear error on failure."""
    raw = os.environ.get(name, default)
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


@dataclass
class SwarmBusConfig:
    """Runtime configuration for the swarm bus.

    Priority (highest to lowest):
    1. Explicit constructor arguments
    2. Environment variables (SWARM_BUS_*)
    3. Built-in defaults
    """

    bus_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("SWARM_BUS_DIR", "/mnt/shared-storage/swarm")
        )
    )
    bus_max_lines: int = field(
        default_factory=lambda: _env_int("SWARM_BUS_MAX_LINES", "500")
    )
    seen_max_entries: int = field(
        default_factory=lambda: _env_int("SWARM_BUS_SEEN_MAX_ENTRIES", "1000")
    )
    seen_keep_entries: int = field(
        default_factory=lambda: _env_int("SWARM_BUS_SEEN_KEEP_ENTRIES", "500")
    )
    tail_lines: int = field(
        default_factory=lambda: _env_int("SWARM_BUS_TAIL_LINES", "100")
    )
    publish_rate_limit_seconds: int = field(
        default_factory=lambda: _env_int("SWARM_BUS_RATE_LIMIT_SECONDS", "30")
    )

    @property
    def bus_file(self) -> Path:
        return self.bus_dir / "bus.jsonl"

    @property
    def agents_dir(self) -> Path:
        return self.bus_dir / "agents"

    def seen_file(self, agent: str) -> Path:
        return self.agents_dir / f"{agent}.seen"

    def validate(self) -> None:
        """Raise ValueError for invalid config values."""
        if self.bus_max_lines < 10:
            raise ValueError(f"bus_max_lines must be ≥10, got {self.bus_max_lines}")
        if self.seen_max_entries < 1:
            raise ValueError(f"seen_max_entries must be ≥1, got {self.seen_max_entries}")
        if self.seen_keep_entries < 1:
            raise ValueError(f"seen_keep_entries must be ≥1, got {self.seen_keep_entries}")
        if self.tail_lines < 1:
            raise ValueError(f"tail_lines must be ≥1, got {self.tail_lines}")
        if self.publish_rate_limit_seconds < 1:
            raise ValueError(
                "publish_rate_limit_seconds must be ≥1, got "
                f"{self.publish_rate_limit_seconds}"
            )
        if self.seen_max_entries < self.seen_keep_entries:
            raise ValueError(
                f"seen_max_entries ({self.seen_max_entries}) must be ≥ "
                f"seen_keep_entries ({self.seen_keep_entries})"
            )
