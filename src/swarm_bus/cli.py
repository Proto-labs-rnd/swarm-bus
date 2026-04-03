"""CLI entry point for swarm-bus."""

from __future__ import annotations

import json
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

import argparse

from swarm_bus import __version__
from swarm_bus.bus import SwarmBus
from swarm_bus.config import SwarmBusConfig
from swarm_bus.models import MessageType


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swarm-bus",
        description="Lightweight inter-agent message bus for homelab agent networks.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--bus-dir",
        default=None,
        metavar="DIR",
        help="Path to the swarm bus directory (default: /mnt/shared-storage/swarm or SWARM_BUS_DIR env)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output messages as JSON lines",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: WARNING)",
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # -- write --
    write_p = sub.add_parser("write", help="Write a message to an agent or broadcast")
    write_p.add_argument("from_agent", metavar="FROM", help="Sender agent name")
    write_p.add_argument("to", metavar="TO", help='Recipient agent name or "all"')
    write_p.add_argument(
        "type",
        metavar="TYPE",
        choices=MessageType.values(),
        help="Message type: " + " | ".join(MessageType.values()),
    )
    write_p.add_argument("payload", metavar="PAYLOAD", help="Message body (plain text)")

    # -- read --
    read_p = sub.add_parser("read", help="Read pending messages for an agent")
    read_p.add_argument("agent", metavar="AGENT", help="Agent name to read messages for")

    # -- stats --
    sub.add_parser("stats", help="Show bus statistics")

    # -- drain --
    drain_p = sub.add_parser(
        "drain",
        help="Read all pending messages for an agent and print them",
    )
    drain_p.add_argument("agent", metavar="AGENT")

    # -- history --
    hist_p = sub.add_parser("history", help="Show recent messages for an agent without marking seen")
    hist_p.add_argument("agent", metavar="AGENT")
    hist_p.add_argument("--limit", type=int, default=20, help="Max messages to show (default: 20)")

    # -- purge --
    sub.add_parser("purge", help="Delete all bus data (use with caution)")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point. Returns exit code."""
    # Graceful shutdown on signals
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(130))

    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s %(name)s: %(message)s",
    )

    cfg_kwargs = {}
    if args.bus_dir is not None:
        cfg_kwargs["bus_dir"] = Path(args.bus_dir)

    try:
        config = SwarmBusConfig(**cfg_kwargs)
        config.validate()
    except ValueError as exc:
        print(f"[swarm-bus] Configuration error: {exc}", file=sys.stderr)
        return 2

    bus = SwarmBus(config=config)

    if args.command == "write":
        try:
            msg = bus.write(
                from_agent=args.from_agent,
                to=args.to,
                type=MessageType(args.type),
                payload=args.payload,
            )
        except ValueError as exc:
            print(f"[swarm-bus] Error: {exc}", file=sys.stderr)
            return 1
        if args.json:
            print(msg.to_json())
        else:
            print(f"[bus] Written: id={msg.id} from={msg.from_agent} to={msg.to} type={msg.type.value}")
        return 0

    elif args.command in ("read", "drain"):
        agent = args.agent
        count = 0
        for msg in bus.read(agent):
            if args.json:
                print(msg.to_json())
            else:
                print(f"[{msg.type.value.upper()}] from={msg.from_agent} → {msg.payload}")
            count += 1
        if not args.json and count == 0:
            pass  # no output = no pending messages (script-friendly)
        return 0

    elif args.command == "stats":
        data = bus.stats()
        if args.json:
            print(json.dumps(data))
        else:
            print(f"bus_lines : {data['bus_lines']}")
            print(f"agents    : {', '.join(data['agents']) or '(none)'}")
        return 0

    elif args.command == "history":
        msgs = bus.history(args.agent, limit=args.limit)
        for msg in msgs:
            if args.json:
                print(msg.to_json())
            else:
                print(f"[{msg.type.value.upper()}] from={msg.from_agent} → {msg.payload}")
        if not msgs and not args.json:
            print("(no messages)")
        return 0

    elif args.command == "purge":
        bus.purge()
        print("[swarm-bus] Bus purged.")
        return 0

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
