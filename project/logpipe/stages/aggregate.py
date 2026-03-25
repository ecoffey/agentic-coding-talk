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
