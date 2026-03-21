# Implementation Detail: Extract WhereStage to stages/where.py

## § Implementation Detail

Pure refactor — no behaviour changes. Existing tests in `test_query.py` cover `WhereStage` via the CLI and will serve as the regression suite. No new tests needed.

---

### Step 1 — Create `logpipe/stages/where.py`

Create the file with `WhereStage` imported from its new home. Import `Predicate` from `logpipe.query` and `LogRecord` from `logpipe.parser`, matching the style of `stages/window.py`.

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from logpipe.parser import LogRecord
from logpipe.query import Predicate


@dataclass
class WhereStage:
    predicate: Predicate

    def process(self, records: Iterable[LogRecord]) -> Iterable[LogRecord]:
        return (r for r in records if self.predicate(r))
```

---

### Step 2 — Remove `WhereStage` from `logpipe/query.py`

Delete lines 221–226 (the `WhereStage` dataclass). The `Iterable` import in `query.py` is still used by `Stage` and `Pipeline`, so leave it.

Before (lines 220–227):
```python

@dataclass
class WhereStage:
    predicate: Predicate

    def process(self, records: Iterable[LogRecord]) -> Iterable[LogRecord]:
        return (r for r in records if self.predicate(r))


class Pipeline:
```

After:
```python

class Pipeline:
```

---

### Step 3 — Update import in `logpipe/cli.py`

Line 9, change:
```python
from logpipe.query import Pipeline, Stage, WhereStage, parse_predicate
```
to:
```python
from logpipe.query import Pipeline, Stage, parse_predicate
from logpipe.stages.where import WhereStage
```

---

### Step 4 — Update `ARCHITECTURE.md` § Module Layout (target state)

Lines 233–242. Change:
```
logpipe/
  parser.py        LogRecord, parse_line()              (done)
  query.py         Stage, Pipeline, WhereStage,         (done)
                   expression parsers
  stages/
    window.py      WindowSpec, WindowBucket,            (done)
                   WindowStage, parse_duration()
  cli.py           ingest + query commands               (extending)
```

To:
```
logpipe/
  parser.py        LogRecord, parse_line()              (done)
  query.py         Stage, Pipeline, Predicate,          (done)
                   expression parsers
  stages/
    where.py       WhereStage                           (done)
    window.py      WindowSpec, WindowBucket,            (done)
                   WindowStage, parse_duration()
  cli.py           ingest + query commands               (extending)
```

---

### Step 5 — Run tests

```bash
cd project && python -m pytest tests/test_query.py tests/test_window.py -v
```

All existing tests should pass unchanged.

---

### No comment updates needed

No inline comments in any file reference `WhereStage`'s location.
