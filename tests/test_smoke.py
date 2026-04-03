import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _patched_script(name: str, tmp_path: Path) -> Path:
    src = (PROJECT_ROOT / name).read_text()
    patched = src.replace('/mnt/shared-storage/swarm', str(tmp_path / 'swarm'))
    dest = tmp_path / name
    dest.write_text(patched)
    dest.chmod(0o755)
    return dest


def test_readme_documents_all_primary_scripts():
    readme = (PROJECT_ROOT / 'README.md').read_text()
    assert 'swarm-bus-read.sh' in readme
    assert 'swarm-bus-write.sh' in readme
    assert 'swarm-publish.sh' in readme


def test_write_script_appends_valid_json_message(tmp_path: Path):
    script = _patched_script('swarm-bus-write.sh', tmp_path)
    result = subprocess.run(
        [str(script), 'proto', 'orion', 'inform', 'hello'],
        check=True,
        capture_output=True,
        text=True,
    )
    bus_file = tmp_path / 'swarm' / 'bus.jsonl'
    assert bus_file.exists()
    lines = bus_file.read_text().strip().splitlines()
    assert len(lines) == 1
    msg = json.loads(lines[0])
    assert msg['from'] == 'proto'
    assert msg['to'] == 'orion'
    assert msg['type'] == 'inform'
    assert msg['payload'] == 'hello'
    assert '[bus] Written:' in result.stdout


def test_read_script_returns_unseen_targeted_message_once(tmp_path: Path):
    write_script = _patched_script('swarm-bus-write.sh', tmp_path)
    read_script = _patched_script('swarm-bus-read.sh', tmp_path)

    subprocess.run(
        [str(write_script), 'proto', 'orion', 'alert', 'disk hot'],
        check=True,
        capture_output=True,
        text=True,
    )

    first = subprocess.run(
        [str(read_script), 'orion'],
        check=True,
        capture_output=True,
        text=True,
    )
    second = subprocess.run(
        [str(read_script), 'orion'],
        check=True,
        capture_output=True,
        text=True,
    )

    first_lines = [line for line in first.stdout.splitlines() if line.strip()]
    assert len(first_lines) == 1
    msg = json.loads(first_lines[0])
    assert msg['to'] == 'orion'
    assert msg['from'] == 'proto'
    assert second.stdout.strip() == ''


def test_publish_script_contains_rate_limit_and_openclaw_send_path():
    content = (PROJECT_ROOT / 'swarm-publish.sh').read_text()
    assert 'Rate limited' in content
    assert '--channel telegram' in content
    assert '--thread-id "$TOPIC_ID"' in content
