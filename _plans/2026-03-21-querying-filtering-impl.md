# Querying — Filtering (Implementation Detail)

## § Implementation Detail

### Overview of steps

1. Write failing tests in `tests/test_query.py` (RED)
2. Fix existing `test_ingest.py` invocations broken by adding a second typer command
3. Create `logpipe/query.py`
4. Update `logpipe/cli.py` to add the `query` command
5. Run all tests (GREEN)
6. Update `project/README.md`

---

### Step 1 — Write failing tests (`tests/test_query.py`)

Create the file. All tests should fail at this point (the `query` command doesn't exist yet).

First, add a `make_log_line` fixture to `conftest.py` — a builder that constructs a valid log line from keyword arguments with sensible defaults. This keeps test data readable and avoids fragile string replacement chains.

**Addition to `project/tests/conftest.py`** (append after existing fixtures):

```python
@pytest.fixture
def make_log_line():
    """Return a factory for building valid log lines from explicit field values."""
    def _make(
        host: str = "127.0.0.1",
        user: str = "frank",
        timestamp: str = "10/Oct/2000:13:55:36 -0700",
        method: str = "GET",
        path: str = "/index.html",
        protocol: str = "HTTP/1.1",
        status: int = 200,
        bytes: int = 1234,
        response_time: float = 0.021,
    ) -> str:
        return (
            f'{host} - {user} [{timestamp}] '
            f'"{method} {path} {protocol}" '
            f'{status} {bytes} {response_time}'
        )
    return _make
```

Then create `tests/test_query.py`:

```python
# project/tests/test_query.py
import json
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def multi_log(tmp_path, make_log_line):
    """A log file with lines of varying status, method, path, response_time."""
    lines = [
        make_log_line(),                                                       # GET /index.html 200 0.021
        make_log_line(status=404, bytes=0, response_time=0.005),              # GET /index.html 404
        make_log_line(method="POST", status=201, bytes=512, response_time=0.100),  # POST /index.html 201
        make_log_line(path="/api/data", status=500, bytes=0, response_time=2.500), # GET /api/data 500
    ]
    f = tmp_path / "multi.log"
    f.write_text("\n".join(lines) + "\n")
    return f


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_filter_status_eq(run, multi_log):
    stdout, _, code = run("query", "status = 200", str(multi_log))
    assert code == 0
    records = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(records) == 1
    assert all(r["status"] == 200 for r in records)


def test_filter_status_gte(run, multi_log):
    stdout, _, code = run("query", "status >= 400", str(multi_log))
    assert code == 0
    records = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(records) == 2
    assert all(r["status"] >= 400 for r in records)


def test_filter_method(run, multi_log):
    stdout, _, code = run("query", "method = POST", str(multi_log))
    assert code == 0
    records = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(records) == 1
    assert records[0]["method"] == "POST"


def test_filter_combined_and(run, multi_log):
    stdout, _, code = run("query", "status >= 400 AND method = GET", str(multi_log))
    assert code == 0
    records = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(records) == 2
    assert all(r["status"] >= 400 and r["method"] == "GET" for r in records)


def test_filter_or(run, multi_log):
    stdout, _, code = run("query", "status = 200 OR status = 201", str(multi_log))
    assert code == 0
    records = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(records) == 2
    assert all(r["status"] in (200, 201) for r in records)


def test_filter_response_time(run, multi_log):
    stdout, _, code = run("query", "response_time > 1.0", str(multi_log))
    assert code == 0
    records = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(records) == 1
    assert records[0]["response_time"] > 1.0


def test_filter_path_contains(run, multi_log):
    stdout, _, code = run("query", "path ~ /api", str(multi_log))
    assert code == 0
    records = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(records) == 1
    assert "/api" in records[0]["path"]


def test_no_match(run, multi_log):
    stdout, _, code = run("query", "status = 999", str(multi_log))
    assert code == 0
    assert stdout.strip() == ""


def test_stdin_query(run, make_log_line):
    stdout, _, code = run("query", "status = 200", "-", stdin=make_log_line() + "\n")
    assert code == 0
    records = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(records) == 1
    assert records[0]["status"] == 200
```

---

### Step 2 — Fix existing `test_ingest.py` invocations

**Why:** typer's single-command mode routes directly to the sole `@app.command()` without requiring a subcommand name. Once a second command (`query`) is added, typer switches to multi-command mode and requires `ingest` to be specified explicitly. All 6 existing tests call `run(str(log_file))` or `run("-", ...)` — these must become `run("ingest", str(log_file))` and `run("ingest", "-", ...)`.

**Changes to `project/tests/test_ingest.py`** — update every `run(` call:

| Old | New |
|-----|-----|
| `run(str(log_file))` | `run("ingest", str(log_file))` |
| `run("-", stdin=...)` | `run("ingest", "-", stdin=...)` |
| `run(str(bad))` | `run("ingest", str(bad))` |
| `run(str(f))` | `run("ingest", str(f))` |

Exact diff:

```python
# test_single_valid_line
-    stdout, _, code = run(str(log_file))
+    stdout, _, code = run("ingest", str(log_file))

# test_all_fields_present
-    stdout, _, _ = run(str(log_file))
+    stdout, _, _ = run("ingest", str(log_file))

# test_timestamp_is_epoch
-    stdout, _, _ = run(str(log_file))
+    stdout, _, _ = run("ingest", str(log_file))

# test_stdin_input
-    stdout, _, code = run("-", stdin=log_line + "\n")
+    stdout, _, code = run("ingest", "-", stdin=log_line + "\n")

# test_malformed_line_skipped
-    stdout, _, code = run(str(bad))
+    stdout, _, code = run("ingest", str(bad))

# test_mixed_valid_invalid
-    stdout, _, code = run(str(f))
+    stdout, _, code = run("ingest", str(f))
```

---

### Step 3 — Create `logpipe/query.py`

Three design decisions reflected in this file:

**A. `_FIELD_TYPES` introspected from `LogRecord`** — use `typing.get_type_hints()` + `dataclasses.fields()` to derive the coercion map at module load time. For `int | None` fields (i.e. `bytes`), strip `None` from the union via `typing.get_args()` to get the concrete cast type. This ensures the map automatically stays in sync with `LogRecord`.

**B. Parser as a class** — `_ExprParser` holds `self.tokens`, `self.expr`, and `self.pos` as instance variables. Eliminates the `pos = [0]` mutable-list-as-closure hack. Makes future grammar extensions (new node types, parentheses, etc.) natural: just add methods. The public API (`parse_predicate`) remains a free function that constructs and invokes the parser.

**C. No dead `return False` in `_make_predicate`'s inner function** — `_make_predicate` always returns a `Predicate` (the inner `pred` function). The exhaustive `if op == ...` chain handles all 7 ops in `VALID_OPS`; an unknown op can't reach `_make_predicate` because `parse_clause` validates against `VALID_OPS` before constructing `FilterExpr`. The unreachable fallback is replaced with `raise AssertionError` to make the invariant explicit rather than silently returning `False`.

```python
# project/logpipe/query.py
from __future__ import annotations

import dataclasses
import re
import typing
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Literal, Protocol

from logpipe.parser import LogRecord

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

Op = Literal["=", "!=", "<", ">", "<=", ">=", "~"]

Predicate = Callable[[LogRecord], bool]

VALID_OPS: frozenset[str] = frozenset({"=", "!=", "<", ">", "<=", ">=", "~"})

VALID_FIELDS: frozenset[str] = frozenset(
    f.name for f in dataclasses.fields(LogRecord)
)


def _base_type(t: type) -> type:
    """Return the concrete type from T | None (Optional[T]), or T unchanged."""
    args = typing.get_args(t)
    if args:
        return next(a for a in args if a is not type(None))
    return t


# Coercion map derived from LogRecord's own type annotations.
# int | None fields (e.g. bytes) resolve to int.
_FIELD_TYPES: dict[str, type] = {
    name: _base_type(t)
    for name, t in typing.get_type_hints(LogRecord).items()
}

# ---------------------------------------------------------------------------
# Domain object
# ---------------------------------------------------------------------------

@dataclass
class FilterExpr:
    """A single comparison predicate: field op value."""
    field: str
    op: Op
    value: Any  # already coerced to field's native type


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r'"[^"]*"'      # double-quoted string
    r"|'[^']*'"     # single-quoted string
    r"|!=|<=|>="    # two-char operators (must precede single-char)
    r"|[=<>~]"      # single-char operators
    r"|\S+"         # bare words: field names, keywords, unquoted values
)


def _tokenize(expr: str) -> list[str]:
    return _TOKEN_RE.findall(expr)


# ---------------------------------------------------------------------------
# Predicate combinators
# ---------------------------------------------------------------------------

def _and(a: Predicate, b: Predicate) -> Predicate:
    return lambda r: a(r) and b(r)


def _or(a: Predicate, b: Predicate) -> Predicate:
    return lambda r: a(r) or b(r)


# ---------------------------------------------------------------------------
# Value coercion
# ---------------------------------------------------------------------------

def _coerce(field: str, token: str) -> Any:
    """Strip quotes from quoted tokens; otherwise cast to the field's type."""
    if token.startswith('"') or token.startswith("'"):
        return token[1:-1]
    cast = _FIELD_TYPES.get(field, str)
    try:
        return cast(token)
    except (ValueError, TypeError):
        return token


# ---------------------------------------------------------------------------
# Predicate builder
# ---------------------------------------------------------------------------

def _make_predicate(fe: FilterExpr) -> Predicate:
    """
    Build a callable predicate from a FilterExpr.

    Always returns a Predicate. The op is validated against VALID_OPS before
    FilterExpr is constructed, so the match below is exhaustive — the
    AssertionError branch is unreachable in correct usage.
    """
    def pred(record: LogRecord) -> bool:
        val = getattr(record, fe.field, None)
        if val is None:
            return False
        op, cmp = fe.op, fe.value
        if op == "=":   return val == cmp   # noqa: E701
        if op == "!=":  return val != cmp   # noqa: E701
        if op == "<":   return val < cmp    # noqa: E701
        if op == ">":   return val > cmp    # noqa: E701
        if op == "<=":  return val <= cmp   # noqa: E701
        if op == ">=":  return val >= cmp   # noqa: E701
        if op == "~":   return str(cmp).lower() in str(val).lower()  # noqa: E701
        raise AssertionError(f"unreachable op: {fe.op!r}")
    return pred


# ---------------------------------------------------------------------------
# Expression parser  (recursive descent, AND > OR precedence)
# ---------------------------------------------------------------------------

class _ExprParser:
    """
    Stateful recursive-descent parser for filter expressions.

    Grammar:
        expr     := and_expr ("OR" and_expr)*
        and_expr := clause ("AND" clause)*
        clause   := FIELD OP VALUE

    AND binds tighter than OR (standard boolean precedence).

    Implemented as a class so that parser state (tokens, pos) lives in
    instance variables rather than mutable-list closure hacks, and so that
    future grammar extensions (parentheses, new node types) can be added
    as additional methods.
    """

    def __init__(self, expr: str) -> None:
        self.expr = expr
        self.tokens = _tokenize(expr.strip())
        self.pos = 0

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, context: str = "token") -> str:
        if self.pos >= len(self.tokens):
            raise ValueError(
                f"Unexpected end of expression (expected {context}): {self.expr!r}"
            )
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse_clause(self) -> Predicate:
        field = self.consume("field name")
        if field.upper() in ("AND", "OR"):
            raise ValueError(
                f"Expected field name, got keyword {field!r} in: {self.expr!r}"
            )
        if field not in VALID_FIELDS:
            raise ValueError(
                f"Unknown field {field!r}. Valid fields: {sorted(VALID_FIELDS)}"
            )
        op = self.consume("operator")
        if op not in VALID_OPS:
            raise ValueError(
                f"Unknown operator {op!r}. Valid operators: {sorted(VALID_OPS)}"
            )
        value_tok = self.consume("value")
        fe = FilterExpr(field=field, op=op, value=_coerce(field, value_tok))  # type: ignore[arg-type]
        return _make_predicate(fe)

    def parse_and(self) -> Predicate:
        left = self.parse_clause()
        while self.peek() and self.peek().upper() == "AND":  # type: ignore[union-attr]
            self.consume()
            right = self.parse_clause()
            left = _and(left, right)
        return left

    def parse_or(self) -> Predicate:
        left = self.parse_and()
        while self.peek() and self.peek().upper() == "OR":  # type: ignore[union-attr]
            self.consume()
            right = self.parse_and()
            left = _or(left, right)
        return left

    def parse(self) -> Predicate:
        predicate = self.parse_or()
        if self.pos < len(self.tokens):
            raise ValueError(
                f"Unexpected token {self.tokens[self.pos]!r} in: {self.expr!r}"
            )
        return predicate


def parse_predicate(expr: str) -> Predicate:
    """Parse a filter expression string into a callable predicate."""
    return _ExprParser(expr).parse()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class Stage(Protocol):
    def process(self, records: Iterable[Any]) -> Iterable[Any]: ...


@dataclass
class WhereStage:
    predicate: Predicate

    def process(self, records: Iterable[LogRecord]) -> Iterable[LogRecord]:
        return (r for r in records if self.predicate(r))


class Pipeline:
    def __init__(self, stages: list[Stage]) -> None:
        self.stages = stages

    def run(self, source: Iterable[Any]) -> Iterable[Any]:
        stream: Iterable[Any] = source
        for stage in self.stages:
            stream = stage.process(stream)
        return stream
```

---

### Step 4 — Update `logpipe/cli.py`

Add import of query types and add the `query` command. Full file after changes:

```python
# project/logpipe/cli.py
import json
import sys
from dataclasses import asdict
from typing import Annotated

import typer

from logpipe.parser import parse_line
from logpipe.query import Pipeline, WhereStage, parse_predicate

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


@app.command()
def query(
    expr: Annotated[str, typer.Argument(help="Filter expression, e.g. 'status >= 400 AND method = POST'")],
    source: Annotated[str, typer.Argument(help="Log file path, or - for stdin")],
):
    """Query log records with a filter expression."""
    pipeline = Pipeline([WhereStage(parse_predicate(expr))])
    fh = sys.stdin if source == "-" else open(source)
    try:
        raw_records = (parse_line(line) for line in fh)
        valid_records = (r for r in raw_records if r is not None)
        for record in pipeline.run(valid_records):
            print(json.dumps(asdict(record)))
    finally:
        if fh is not sys.stdin:
            fh.close()


if __name__ == "__main__":
    app()
```

---

### Step 5 — Run tests

```bash
cd project && uv run pytest
```

Expected: all 15 tests pass (6 existing `test_ingest` + 9 new `test_query`).

---

### Step 6 — Update `project/README.md`

Add a `### Query logs` section after the existing `### Ingest logs` section. Insert between line 31 (`Malformed lines are silently skipped.`) and line 33 (`## Run tests`):

```markdown
### Query logs

Filter log records with a WHERE expression:

```bash
uv run logpipe query "status >= 400" access.log
uv run logpipe query "status >= 400" -     # read from stdin
```

Expressions support `=`, `!=`, `<`, `>`, `<=`, `>=` (numeric/string), and `~` (substring):

```bash
uv run logpipe query "status >= 400 AND method = POST" access.log
uv run logpipe query "status = 200 OR status = 201" access.log
uv run logpipe query "path ~ /api" access.log
uv run logpipe query "response_time > 1.0" access.log
```

Filterable fields: `host`, `user`, `ts`, `method`, `path`, `status`, `bytes`, `response_time`.

Output is one JSON object per matching line. Non-matching lines produce no output.
```

Also update the `### Ingest logs` invocation examples to use the explicit subcommand, since `ingest` is now required when multiple commands exist:

```bash
# Before
uv run logpipe access.log
uv run logpipe -

# After
uv run logpipe ingest access.log
uv run logpipe ingest -
```

---

### Files touched (summary)

| File | Action |
|------|--------|
| `project/tests/conftest.py` | Add `make_log_line` fixture |
| `project/tests/test_query.py` | Create (9 tests) |
| `project/tests/test_ingest.py` | Update all 6 `run(` calls to include `"ingest"` |
| `project/logpipe/query.py` | Create |
| `project/logpipe/cli.py` | Add `query` command + import |
| `project/README.md` | Add `query` section; update `ingest` invocations |

---

### Feedback Log

> instead of changing a string, lets write a builder for generating test log lines
>
> Context: appeared after the `multi_log` fixture which used `log_line.replace(...)` chains. Resolved by adding a `make_log_line` fixture to `conftest.py` — a factory function with keyword args and defaults for every log field. `multi_log` and `test_stdin_query` now use it.

---

> can this be part of the LogRecord class instead? or introspected from that class at runtime?
>
> Context: appeared after the hardcoded `_FIELD_TYPES: dict[str, type]` mapping. Resolved by deriving it at module load time via `typing.get_type_hints(LogRecord)`, with a `_base_type()` helper that strips `None` from union types (e.g. `int | None` → `int`) so coercion still works for the optional `bytes` field.

---

> why is this returning False or a Predicate? Wouldn't Optional[Predicate] be a better return type?
>
> Context: appeared on `_make_predicate`. Clarification: `_make_predicate` always returns a `Predicate` — the `return False` the user saw is inside the inner `pred` function (what `pred` returns when `val is None`), not what `_make_predicate` itself returns. The return type is correct as `Predicate`. The unreachable fallback `return False` at the end of the op chain has been replaced with `raise AssertionError(f"unreachable op: {fe.op!r}")` to make the invariant explicit.

---

> why is this a single int in an array? is it because the inner functions are closing over it and the array is how you share the mutations with the other closures? if so maybe its better to have the parser be a class? would that make future work on query more extensible?
>
> Context: appeared on `pos = [0]` inside `parse_predicate`. Yes — exactly that reason: Python closures can read but not rebind names from an enclosing scope without `nonlocal`; wrapping in a list was the workaround. Resolved by converting the parser to `_ExprParser` class: `self.pos`, `self.tokens`, `self.expr` are instance variables; `peek`, `consume`, `parse_clause`, `parse_and`, `parse_or`, `parse` are methods. Future grammar extensions (parentheses, new operators) add as new methods. The public `parse_predicate(expr)` free function constructs and invokes the class.
