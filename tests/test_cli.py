"""CLI integration tests for swarm-bus."""

import json
import pytest
from pathlib import Path

from swarm_bus.cli import main


@pytest.fixture
def bus_dir(tmp_path: Path) -> str:
    return str(tmp_path / "swarm")


def test_cli_write_and_read(bus_dir: str):
    rc = main(["--bus-dir", bus_dir, "write", "proto", "orion", "inform", "hello"])
    assert rc == 0

    output = []
    import io, sys
    old = sys.stdout
    sys.stdout = io.StringIO()
    rc2 = main(["--bus-dir", bus_dir, "--json", "read", "orion"])
    captured = sys.stdout.getvalue()
    sys.stdout = old

    assert rc2 == 0
    line = captured.strip()
    assert line  # at least one line
    msg = json.loads(line)
    assert msg["payload"] == "hello"
    assert msg["from"] == "proto"


def test_cli_write_json_output(bus_dir: str, capsys):
    rc = main(["--bus-dir", bus_dir, "--json", "write", "proto", "orion", "alert", "boom"])
    out, _ = capsys.readouterr()
    assert rc == 0
    data = json.loads(out.strip())
    assert data["type"] == "alert"
    assert data["payload"] == "boom"


def test_cli_read_empty_bus(bus_dir: str, capsys):
    rc = main(["--bus-dir", bus_dir, "read", "orion"])
    out, _ = capsys.readouterr()
    assert rc == 0
    assert out == ""


def test_cli_stats(bus_dir: str, capsys):
    main(["--bus-dir", bus_dir, "write", "proto", "orion", "inform", "hi"])
    capsys.readouterr()  # flush write output
    rc = main(["--bus-dir", bus_dir, "--json", "stats"])
    out, _ = capsys.readouterr()
    assert rc == 0
    data = json.loads(out.strip())
    assert data["bus_lines"] == 1


def test_cli_write_missing_payload_error(bus_dir: str, capsys):
    rc = main(["--bus-dir", bus_dir, "write", "proto", "orion", "inform", "   "])
    _, err = capsys.readouterr()
    assert rc == 1
    assert "Error" in err


def test_cli_invalid_bus_max_lines_error(bus_dir: str, capsys, monkeypatch):
    monkeypatch.setenv("SWARM_BUS_MAX_LINES", "3")
    rc = main(["--bus-dir", bus_dir, "write", "proto", "orion", "inform", "hi"])
    _, err = capsys.readouterr()
    assert rc == 2
    assert "Configuration error" in err
    monkeypatch.delenv("SWARM_BUS_MAX_LINES")


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    out, _ = capsys.readouterr()
    assert "0.5.0" in out


def test_cli_drain_alias(bus_dir: str, capsys):
    main(["--bus-dir", bus_dir, "write", "proto", "orion", "inform", "drain-test"])
    rc = main(["--bus-dir", bus_dir, "drain", "orion"])
    out, _ = capsys.readouterr()
    assert rc == 0
    assert "drain-test" in out


def test_cli_history_no_messages_prints_placeholder(bus_dir: str, capsys):
    rc = main(["--bus-dir", bus_dir, "history", "orion"])
    out, _ = capsys.readouterr()
    assert rc == 0
    assert "(no messages)" in out
