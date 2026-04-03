# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] — 2026-04-03

### Added
- GitHub Actions CI workflow for test validation on push / pull request
- Stricter configuration validation for environment-driven integers and bounds

### Changed
- Version synced: `pyproject.toml` → `0.5.0`
- `history` CLI prints empty-state output to stdout for scriptability

## [0.4.0] — 2026-04-03

### Added
- MIT LICENSE file
- `examples/basic_usage.py` with annotated walkthrough
- `CONTRIBUTING.md` with dev/test/PR guidelines
- Agent name sanitization (reject path traversal and special chars)
- Signal handling (SIGTERM/SIGINT graceful shutdown in CLI)
- `BusMessage.__eq__` for test ergonomics
- `SwarmBus.purge()` method to clear all bus state
- `SwarmBus.history(agent, limit)` for re-reading recent messages without marking seen
- `.editorconfig` for consistent style

### Changed
- Version synced: `pyproject.toml` → `0.4.0`
- CLI returns meaningful exit codes (0=ok, 1=usage error, 2=config error)

## [0.3.0] — 2026-04-02

### Added
- Python CLI with `write`, `read`, `drain`, `stats` subcommands
- `--json`, `--bus-dir`, `--log-level` CLI options
- `SwarmBusConfig` with env-var overrides and validation
- Atomic writes for bus rotation and seen-file trimming
- 48 unit tests

## [0.2.0] — 2026-04-01

### Added
- `SwarmBus` Python class (write / read / rotate / trim / stats)
- `BusMessage` model with JSON serialization
- `MessageType` enum (ask, inform, alert, ack)

## [0.1.0] — 2026-03-30

### Added
- Initial shell-based bus scripts (`swarm-bus-write.sh`, `swarm-bus-read.sh`)
- Append-only JSONL format
- Per-agent seen-file tracking
