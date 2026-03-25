# Implementation Detail: AGGREGATE Stage

## § Implementation Detail

---

### Step 1 — Create `logpipe/stages/aggregate.py`

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from logpipe.parser import LogRecord
from logpipe.stages.window import WindowBucket

# Fields for which we compute sum/avg/min/max
NUMERIC_FIELDS = ("bytes", "response_time")


def _aggregate_records(records: list[LogRecord], group_by: list[str]) -> list[dict]:
    """Group records by group_by fields and compute aggregate stats."""
    groups: dict[tuple, dict[str, Any]] = {}

    for r in records:
        key = tuple(getattr(r, f) for f in group_by)
        if key not in groups:
            entry: dict[str, Any] = {f: getattr(r, f) for f in group_by}
            entry["count"] = 0
            for field in NUMERIC_FIELDS:
                entry[f"_{field}_values"] = []
            groups[key] = entry
        g = groups[key]
        g["count"] += 1
        for field in NUMERIC_FIELDS:
            val = getattr(r, field, None)
            if val is not None:
                g[f"_{field}_values"].append(val)

    results = []
    for g in groups.values():
        row: dict[str, Any] = {k: v for k, v in g.items() if not k.startswith("_")}
        for field in NUMERIC_FIELDS:
            vals = g[f"_{field}_values"]
            if vals:
                row[f"{field}_sum"] = sum(vals)
                row[f"{field}_avg"] = sum(vals) / len(vals)
                row[f"{field}_min"] = min(vals)
                row[f"{field}_max"] = max(vals)
        results.append(row)

    return results


@dataclass
class AggregateStage:
    group_by: list[str]

    def process(
        self, records: Iterable[LogRecord | WindowBucket]
    ) -> Iterable[dict]:
        peeked = list(records)
        if not peeked:
            return

        if isinstance(peeked[0], WindowBucket):
            for bucket in peeked:
                assert isinstance(bucket, WindowBucket)
                for row in _aggregate_records(bucket.records, self.group_by):
                    yield {"window_start": bucket.window_start,
                           "window_end": bucket.window_end,
                           **row}
        else:
            log_records = [r for r in peeked if isinstance(r, LogRecord)]
            yield from _aggregate_records(log_records, self.group_by)
```

---

### Step 2 — Write failing tests in `tests/test_aggregate.py`

```python
import json

import pytest


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

TS_BUCKET_2 = "10/Oct/2000:14:01:36 -0700"
BUCKET_1_START = 971211300
BUCKET_1_END   = 971211600
BUCKET_2_START = 971211600
BUCKET_2_END   = 971211900


@pytest.fixture
def two_host_log(tmp_path, make_log_line):
    """Three records: 2 from host-a, 1 from host-b."""
    lines = [
        make_log_line(host="host-a", status=200, bytes=1000, response_time=0.1),
        make_log_line(host="host-a", status=404, bytes=500,  response_time=0.2),
        make_log_line(host="host-b", status=200, bytes=800,  response_time=0.05),
    ]
    f = tmp_path / "two_host.log"
    f.write_text("\n".join(lines) + "\n")
    return f


@pytest.fixture
def window_two_host_log(tmp_path, make_log_line):
    """
    Two buckets, two hosts each:
      bucket1: host-a 200, host-b 404
      bucket2: host-a 500
    """
    lines = [
        make_log_line(host="host-a", status=200, bytes=1000, response_time=0.1),
        make_log_line(host="host-b", status=404, bytes=500,  response_time=0.2),
        make_log_line(host="host-a", status=500, bytes=200,  response_time=0.5,
                      timestamp=TS_BUCKET_2),
    ]
    f = tmp_path / "window_two_host.log"
    f.write_text("\n".join(lines) + "\n")
    return f


# ---------------------------------------------------------------------------
# Basic GROUP BY tests (no window)
# ---------------------------------------------------------------------------

def test_group_by_produces_one_row_per_group(run, two_host_log):
    stdout, _, code = run("query", "status >= 200", "--group-by", "host",
                          str(two_host_log))
    assert code == 0
    rows = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    hosts = {r["host"] for r in rows}
    assert hosts == {"host-a", "host-b"}
    assert len(rows) == 2


def test_group_by_count(run, two_host_log):
    stdout, _, code = run("query", "status >= 200", "--group-by", "host",
                          str(two_host_log))
    assert code == 0
    rows = {r["host"]: r for r in
            [json.loads(l) for l in stdout.splitlines() if l.strip()]}
    assert rows["host-a"]["count"] == 2
    assert rows["host-b"]["count"] == 1


def test_group_by_numeric_stats(run, two_host_log):
    stdout, _, code = run("query", "status >= 200", "--group-by", "host",
                          str(two_host_log))
    assert code == 0
    rows = {r["host"]: r for r in
            [json.loads(l) for l in stdout.splitlines() if l.strip()]}
    a = rows["host-a"]
    assert a["bytes_sum"] == 1500
    assert a["bytes_min"] == 500
    assert a["bytes_max"] == 1000
    assert abs(a["response_time_avg"] - 0.15) < 1e-9


def test_group_by_no_match(run, two_host_log):
    stdout, _, code = run("query", "status = 999", "--group-by", "host",
                          str(two_host_log))
    assert code == 0
    assert stdout.strip() == ""


def test_group_by_multi_field(run, tmp_path, make_log_line):
    lines = [
        make_log_line(host="h1", method="GET"),
        make_log_line(host="h1", method="POST"),
        make_log_line(host="h1", method="GET"),
    ]
    f = tmp_path / "multi.log"
    f.write_text("\n".join(lines) + "\n")
    stdout, _, code = run("query", "status >= 200", "--group-by", "host,method",
                          str(f))
    assert code == 0
    rows = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(rows) == 2
    counts = {(r["host"], r["method"]): r["count"] for r in rows}
    assert counts[("h1", "GET")] == 2
    assert counts[("h1", "POST")] == 1


# ---------------------------------------------------------------------------
# GROUP BY + WINDOW
# ---------------------------------------------------------------------------

def test_group_by_with_window(run, window_two_host_log):
    stdout, _, code = run("query", "status >= 200",
                          "--window", "5m",
                          "--group-by", "host",
                          str(window_two_host_log))
    assert code == 0
    rows = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    # bucket1: host-a(1), host-b(1) → 2 rows; bucket2: host-a(1) → 1 row
    assert len(rows) == 3


def test_group_by_with_window_metadata(run, window_two_host_log):
    stdout, _, code = run("query", "status >= 200",
                          "--window", "5m",
                          "--group-by", "host",
                          str(window_two_host_log))
    assert code == 0
    rows = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    for row in rows:
        assert "window_start" in row
        assert "window_end" in row
    b1_rows = [r for r in rows if r["window_start"] == BUCKET_1_START]
    b2_rows = [r for r in rows if r["window_start"] == BUCKET_2_START]
    assert len(b1_rows) == 2
    assert len(b2_rows) == 1
```

---

### Step 3 — Update `logpipe/cli.py`

Add `--group-by` option and wire `AggregateStage` into the pipeline.

**Add import** (line 11, after window import):
```python
from logpipe.stages.aggregate import AggregateStage
```

**Replace the `query` function signature** to add `group_by`:
```python
@app.command()
def query(
    expr: Annotated[str, typer.Argument(help="Filter expression, e.g. 'status >= 400 AND method = POST'")],
    source: Annotated[str, typer.Argument(help="Log file path, or - for stdin")],
    window: Annotated[str | None, typer.Option("--window", help="Tumbling window size, e.g. 5m, 1h, 30s")] = None,
    group_by: Annotated[str | None, typer.Option("--group-by", help="Comma-separated field(s) to group by, e.g. 'host' or 'host,method'")] = None,
):
```

**Replace pipeline construction block** (currently lines 39–41):
```python
    stages: list[Stage] = [WhereStage(parse_predicate(expr))]
    if window is not None:
        stages.append(WindowStage(WindowSpec(size_secs=parse_duration(window))))
    if group_by is not None:
        fields = [f.strip() for f in group_by.split(",")]
        stages.append(AggregateStage(fields))
```

**Replace the output loop** (currently lines 48–57):
```python
        for item in pipeline.run(valid_records):
            if isinstance(item, dict):
                print(json.dumps(item))
            elif isinstance(item, WindowBucket):
                print(json.dumps({
                    "window_start": item.window_start,
                    "window_end": item.window_end,
                    "count": len(item.records),
                    "records": [asdict(r) for r in item.records],
                }))
            else:
                print(json.dumps(asdict(item)))
```

---

### Step 4 — Update `ARCHITECTURE.md`

**In `## SQL-Style Execution Order` table**, change AGGREGATE row:

```
| AGGREGATE | `--group-by`, aggregate functions in SELECT | Future | ...
```
→
```
| AGGREGATE | `--group-by` | Implemented | Group records and compute aggregates (count, sum, avg, min, max for numeric fields) within each window if WINDOW is active |
```

**In `## Module Layout (target state)`**, add after `window.py` line:

```
    aggregate.py   AggregateStage, NUMERIC_FIELDS,           (done)
                   _aggregate_records()
```

---

### Step 5 — Run full test suite to verify

```bash
cd project && python -m pytest tests/ -v
```

All existing tests should still pass; new `test_aggregate.py` tests should pass after Step 1–3.
