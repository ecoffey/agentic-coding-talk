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
