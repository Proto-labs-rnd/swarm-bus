# Contributing to swarm-bus

Thanks for your interest! Here's how to contribute.

## Development Setup

```bash
git clone <repo-url>
cd swarm-bus
pip install -e ".[test]"
```

## Running Tests

```bash
PYTHONPATH=src pytest tests/ -v
```

All 48+ tests should pass. Tests use temporary directories and don't touch the real bus.

## Code Style

- Python 3.9+ compatible
- Type hints on all public functions
- `logging` module (no bare `print` in library code)
- `black` formatting, `isort` for imports
- Max line length: 100

## Pull Request Process

1. Create a feature branch from `main`
2. Add tests for any new functionality
3. Ensure all existing tests pass
4. Update `CHANGELOG.md` under "Unreleased"
5. Open PR with a clear description

## Adding a New Message Type

1. Add entry to `MessageType` enum in `models.py`
2. Add validation in `BusMessage` if needed
3. Add CLI support in `cli.py`
4. Add tests in `test_models.py` and `test_cli.py`

## Reporting Issues

- Include Python version, OS, and bus configuration
- Include relevant log output with `--log-level DEBUG`
