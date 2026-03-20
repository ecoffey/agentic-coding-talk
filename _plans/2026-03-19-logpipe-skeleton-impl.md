# logpipe Skeleton — Implementation Detail

## § Implementation Detail

Follow in order. Write tests first (all RED), then implement until GREEN.

---

### Step 1 — `project/pyproject.toml`

**File:** `project/pyproject.toml` (new)

```toml
[project]
name = "logpipe"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["typer"]

[project.scripts]
logpipe = "logpipe.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
testpaths = ["tests"]

[dependency-groups]
dev = ["pytest"]
```

---

### Step 2 — `project/logpipe/__init__.py`

**File:** `project/logpipe/__init__.py` (new, empty)

```python
```

---

### Step 3 — `project/tests/conftest.py`

**File:** `project/tests/conftest.py` (new)

```python
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def run(tmp_path):
    """Run `logpipe` as a subprocess. Returns (stdout, stderr, returncode)."""
    def _run(*args, stdin: str | None = None):
        result = subprocess.run(
            [sys.executable, "-m", "logpipe", *args],
            input=stdin,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        return result.stdout, result.stderr, result.returncode

    return _run


@pytest.fixture
def log_line():
    return '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.1" 200 1234 0.021'


@pytest.fixture
def log_file(tmp_path, log_line):
    f = tmp_path / "access.log"
    f.write_text(log_line + "\n")
    return f
```

---

### Step 4 — `project/tests/test_ingest.py` (RED)

**File:** `project/tests/test_ingest.py` (new)

```python
import json


def test_single_valid_line(run, log_file):
    stdout, _, code = run("ingest", str(log_file))
    assert code == 0
    lines = [l for l in stdout.splitlines() if l.strip()]
    assert len(lines) == 1


def test_all_fields_present(run, log_file):
    stdout, _, _ = run("ingest", str(log_file))
    record = json.loads(stdout.strip())
    assert set(record.keys()) == {"host", "user", "ts", "method", "path", "status", "bytes", "response_time"}


def test_timestamp_is_epoch(run, log_file):
    stdout, _, _ = run("ingest", str(log_file))
    record = json.loads(stdout.strip())
    assert isinstance(record["ts"], int)
    assert record["ts"] == 971186136


def test_stdin_input(run, log_line):
    stdout, _, code = run("ingest", "-", stdin=log_line + "\n")
    assert code == 0
    record = json.loads(stdout.strip())
    assert record["path"] == "/index.html"


def test_malformed_line_skipped(run, tmp_path):
    bad = tmp_path / "bad.log"
    bad.write_text("this is not a log line\n")
    stdout, _, code = run("ingest", str(bad))
    assert code == 0
    assert stdout.strip() == ""


def test_mixed_valid_invalid(run, tmp_path, log_line):
    f = tmp_path / "mixed.log"
    f.write_text(
        log_line + "\n"
        "not a log line\n"
        + log_line.replace("/index.html", "/about.html") + "\n"
    )
    stdout, _, code = run("ingest", str(f))
    assert code == 0
    lines = [l for l in stdout.splitlines() if l.strip()]
    assert len(lines) == 2
    paths = [json.loads(l)["path"] for l in lines]
    assert "/index.html" in paths
    assert "/about.html" in paths
```

---

### Step 5 — Install deps and verify RED

```bash
cd project
pip install -e ".[dev]"   # or: pip install -e . && pip install pytest
pytest                    # expect: 6 failures (ImportError on logpipe.cli)
```

---

### Step 6 — `project/logpipe/parser.py` (GREEN)

**File:** `project/logpipe/parser.py` (new)

```python
import re
from dataclasses import dataclass
from datetime import datetime, timezone

LOG_PATTERN = re.compile(
    r'(?P<host>\S+) \S+ (?P<user>\S+) \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d{3}) (?P<bytes>\d+|-) '
    r'(?P<response_time>\d+(?:\.\d+)?)'
)

TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


@dataclass
class LogRecord:
    host: str
    user: str
    ts: int
    method: str
    path: str
    status: int
    bytes: int | None
    response_time: float


def parse_line(line: str) -> LogRecord | None:
    m = LOG_PATTERN.match(line.strip())
    if not m:
        return None
    d = m.groupdict()
    try:
        ts = int(datetime.strptime(d["timestamp"], TIMESTAMP_FORMAT).timestamp())
    except ValueError:
        return None
    return LogRecord(
        host=d["host"],
        user=d["user"],
        ts=ts,
        method=d["method"],
        path=d["path"],
        status=int(d["status"]),
        bytes=int(d["bytes"]) if d["bytes"] != "-" else None,
        response_time=float(d["response_time"]),
    )
```

---

### Step 7 — `project/logpipe/cli.py` (GREEN)

**File:** `project/logpipe/cli.py` (new)

```python
import json
import sys
from dataclasses import asdict
from typing import Annotated

import typer

from logpipe.parser import parse_line

app = typer.Typer()


@app.command()
def ingest(
    source: Annotated[str, typer.Argument(help="Log file path, or - for stdin")],
):
    """Parse log lines and echo them as JSON to stdout."""
    fh = sys.stdin if source == "-" else open(source)
    try:
        for line in fh:
            record = parse_line(line)
            if record is not None:
                print(json.dumps(asdict(record)))
    finally:
        if fh is not sys.stdin:
            fh.close()


if __name__ == "__main__":
    app()
```

---

### Step 8 — Run tests (expect GREEN)

```bash
cd project
pytest -v
```

All 6 tests should pass.

---

### Step 9 — `project/README.md` (new)

**File:** `project/README.md` (new)

```markdown
# logpipe

A log analytics CLI built as a demo for ATLS 4214.

## Setup

Requires Python 3.11+.

```bash
cd project
pip install -e .
```

## Usage

### Ingest logs

Parse log lines and echo them as JSON:

```bash
logpipe ingest access.log
logpipe ingest -          # read from stdin
```

Output is one JSON object per valid line:

```json
{"host": "127.0.0.1", "user": "-", "ts": 971186136, "method": "GET", "path": "/index.html", "status": 200, "bytes": 1234, "response_time": 0.021}
```

Malformed lines are silently skipped.

## Run tests

```bash
pip install pytest
pytest
```

## Log format

Expects Extended Combined Log Format — standard Apache/nginx access logs with an
appended `response_time` field (seconds):

```
127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.1" 200 1234 0.021
```
```

---

### Files created summary

| File | Action |
|---|---|
| `project/pyproject.toml` | Create |
| `project/logpipe/__init__.py` | Create (empty) |
| `project/logpipe/parser.py` | Create |
| `project/logpipe/cli.py` | Create |
| `project/tests/conftest.py` | Create |
| `project/tests/test_ingest.py` | Create |
| `project/README.md` | Create |
