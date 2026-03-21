# Window Stage — Implementation Detail

## § Implementation Detail

---

### Step 1 — Create `logpipe/stages/` package with `window.py`

New directory and files: `project/logpipe/stages/__init__.py` and `project/logpipe/stages/window.py`.

`query.py` keeps `Stage`, `Pipeline`, `WhereStage` unchanged. All window code lives in the new subpackage.

**`project/logpipe/stages/__init__.py`** — empty, just marks it as a package:

```python
```

**`project/logpipe/stages/window.py`**:

```python
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from logpipe.parser import LogRecord

# ---------------------------------------------------------------------------
# Duration parsing
# ---------------------------------------------------------------------------

_DURATION_RE = re.compile(r"^(\d+)(s|m|h)$")


def parse_duration(s: str) -> int:
    """Parse a human-readable duration into seconds. E.g. '5m' → 300."""
    m = _DURATION_RE.match(s.strip())
    if not m:
        raise ValueError(
            f"Invalid duration {s!r} — expected e.g. '5m', '1h', '30s'"
        )
    n, unit = int(m.group(1)), m.group(2)
    return n * {"s": 1, "m": 60, "h": 3600}[unit]


# ---------------------------------------------------------------------------
# Window types
# ---------------------------------------------------------------------------

@dataclass
class WindowSpec:
    size_secs: int  # bucket duration in seconds


@dataclass
class WindowBucket:
    window_start: int        # epoch seconds (inclusive)
    window_end: int          # epoch seconds (exclusive)
    records: list[LogRecord]


class WindowStage:
    def __init__(self, spec: WindowSpec) -> None:
        self.spec = spec

    def process(self, records: Iterable[LogRecord]) -> Iterable[WindowBucket]:
        """Group records into fixed-size tumbling time buckets."""
        buckets: dict[int, list[LogRecord]] = {}
        for r in records:
            key = (r.ts // self.spec.size_secs) * self.spec.size_secs
            buckets.setdefault(key, []).append(r)
        for start in sorted(buckets):
            yield WindowBucket(
                window_start=start,
                window_end=start + self.spec.size_secs,
                records=buckets[start],
            )
```

`query.py` — **no changes needed**.

---

### Step 2 — Update `logpipe/cli.py`

**File:** `project/logpipe/cli.py`

Replace the entire file with:

```python
import json
import sys
from dataclasses import asdict
from typing import Annotated

import typer

from logpipe.parser import parse_log_record
from logpipe.query import Pipeline, WhereStage, parse_predicate
from logpipe.stages.window import WindowBucket, WindowSpec, WindowStage, parse_duration

app = typer.Typer()


@app.command()
def ingest(
    source: Annotated[str, typer.Argument(help="Log file path, or - for stdin")],
):
    """Parse log lines and echo them as JSON to stdout."""
    fh = sys.stdin if source == "-" else open(source)
    try:
        for line in fh:
            record = parse_log_record(line)
            if record is not None:
                print(json.dumps(asdict(record)))
    finally:
        if fh is not sys.stdin:
            fh.close()


@app.command()
def query(
    expr: Annotated[str, typer.Argument(help="Filter expression, e.g. 'status >= 400 AND method = POST'")],
    source: Annotated[str, typer.Argument(help="Log file path, or - for stdin")],
    window: Annotated[str | None, typer.Option("--window", help="Tumbling window size, e.g. 5m, 1h, 30s")] = None,
):
    """Query log records with a filter expression."""
    stages = [WhereStage(parse_predicate(expr))]
    if window is not None:
        stages.append(WindowStage(WindowSpec(size_secs=parse_duration(window))))

    pipeline = Pipeline(stages)
    fh = sys.stdin if source == "-" else open(source)
    try:
        raw_records = (parse_log_record(line) for line in fh)
        valid_records = (r for r in raw_records if r is not None)
        for item in pipeline.run(valid_records):
            if isinstance(item, WindowBucket):
                print(json.dumps({
                    "window_start": item.window_start,
                    "window_end": item.window_end,
                    "count": len(item.records),
                    "records": [asdict(r) for r in item.records],
                }))
            else:
                print(json.dumps(asdict(item)))
    finally:
        if fh is not sys.stdin:
            fh.close()


if __name__ == "__main__":
    app()
```

---

### Step 3 — Create `tests/test_window.py`

**File:** `project/tests/test_window.py`

Timestamp reference (used for expected bucket boundaries):
- `"10/Oct/2000:13:55:36 -0700"` → epoch `971211336`
  - 5-minute bucket: `971211300` → `971211600`
- `"10/Oct/2000:14:01:36 -0700"` → epoch `971211696` (6 min after default)
  - 5-minute bucket: `971211600` → `971211900`

```python
import json
import pytest

# Bucket boundaries for 5-minute (300s) windows
# Default make_log_line timestamp "10/Oct/2000:13:55:36 -0700" → epoch 971211336
BUCKET_1_START = 971211300
BUCKET_1_END = 971211600

# "10/Oct/2000:14:01:36 -0700" → epoch 971211696
BUCKET_2_START = 971211600
BUCKET_2_END = 971211900
TS_BUCKET_2 = "10/Oct/2000:14:01:36 -0700"


@pytest.fixture
def window_log(tmp_path, make_log_line):
    """Log file with records spread across two 5-minute windows."""
    lines = [
        make_log_line(status=200),                              # bucket 1
        make_log_line(status=404),                              # bucket 1
        make_log_line(timestamp=TS_BUCKET_2, status=500),       # bucket 2
    ]
    f = tmp_path / "window.log"
    f.write_text("\n".join(lines) + "\n")
    return f


def test_window_no_match(run, window_log):
    stdout, _, code = run("query", "status = 999", "--window", "5m", str(window_log))
    assert code == 0
    assert stdout.strip() == ""


def test_window_single_bucket(run, tmp_path, make_log_line):
    """All records land in the same window → 1 bucket emitted."""
    lines = [make_log_line(status=200), make_log_line(status=404)]
    f = tmp_path / "single.log"
    f.write_text("\n".join(lines) + "\n")

    stdout, _, code = run("query", "status >= 200", "--window", "5m", str(f))
    assert code == 0
    buckets = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(buckets) == 1
    assert buckets[0]["window_start"] == BUCKET_1_START
    assert buckets[0]["window_end"] == BUCKET_1_END
    assert buckets[0]["count"] == 2
    assert len(buckets[0]["records"]) == 2


def test_window_two_buckets(run, window_log):
    """Records spanning two windows → 2 buckets in chronological order."""
    stdout, _, code = run("query", "status >= 200", "--window", "5m", str(window_log))
    assert code == 0
    buckets = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(buckets) == 2

    assert buckets[0]["window_start"] == BUCKET_1_START
    assert buckets[0]["window_end"] == BUCKET_1_END
    assert buckets[0]["count"] == 2

    assert buckets[1]["window_start"] == BUCKET_2_START
    assert buckets[1]["window_end"] == BUCKET_2_END
    assert buckets[1]["count"] == 1


def test_window_with_where_filter(run, window_log):
    """WHERE runs before WINDOW — only matching records appear in buckets."""
    # window_log has: 200 (bucket1), 404 (bucket1), 500 (bucket2)
    # filter status >= 400 → 404 (bucket1) and 500 (bucket2) survive
    stdout, _, code = run("query", "status >= 400", "--window", "5m", str(window_log))
    assert code == 0
    buckets = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(buckets) == 2
    assert buckets[0]["count"] == 1
    assert buckets[0]["records"][0]["status"] == 404
    assert buckets[1]["count"] == 1
    assert buckets[1]["records"][0]["status"] == 500


def test_window_stdin(run, make_log_line):
    """Window works when reading from stdin."""
    stdin = make_log_line(status=200) + "\n" + make_log_line(status=404) + "\n"
    stdout, _, code = run("query", "status >= 200", "--window", "5m", "-", stdin=stdin)
    assert code == 0
    buckets = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(buckets) == 1
    assert buckets[0]["count"] == 2


def test_window_invalid_duration(run, tmp_path, make_log_line):
    """Bad --window value → non-zero exit."""
    f = tmp_path / "x.log"
    f.write_text(make_log_line() + "\n")
    _, _, code = run("query", "status >= 200", "--window", "5minutes", str(f))
    assert code != 0
```

---

### Step 4 — Update `project/ARCHITECTURE.md`

In the status table (lines 15–22), change the WINDOW row from:

```
| WINDOW | `--window` | Future | Partition stream into time-based buckets before aggregation |
```

to:

```
| WINDOW | `--window` | Implemented (tumbling only) | Partition stream into fixed-size time buckets before aggregation |
```

Also update the non-goals section at the bottom — remove this line:

```
- Windowing / time-bucketing (may be added as a variant of AGGREGATE)
```

Also update the module layout section to reflect the new `stages/` directory:

```
logpipe/
  parser.py        LogRecord, parse_line()              (done)
  query.py         Stage, Pipeline, WhereStage,         (in progress)
                   expression parsers
  stages/
    window.py      WindowSpec, WindowBucket,            (done)
                   WindowStage, parse_duration()
  cli.py           ingest + query commands               (extending)
```

---

### Execution order

1. Create `logpipe/stages/__init__.py` and `logpipe/stages/window.py`
2. Write `tests/test_window.py` → confirm tests **fail** (Red)
3. Update `cli.py`
4. Run tests → confirm they **pass** (Green)
5. Update `ARCHITECTURE.md`

---

### Feedback Log

> **On Step 1 (file layout for window code):**
> "this is looking good, however I think we should re-think the file layout: lets have query.py keep the Stage protocol and pipeline class, but then create a stages/ dir and make a `window.py` file there with this new window code. I'll do a separate /plan to move "where" to its own stage file."
>
> → Incorporated: window code moved to `logpipe/stages/window.py`; `query.py` unchanged. `cli.py` imports from `logpipe.stages.window`.
