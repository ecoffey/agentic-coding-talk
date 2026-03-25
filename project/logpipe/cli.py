import json
import sys
from dataclasses import asdict
from typing import Annotated

import typer

from logpipe.parser import parse_log_record
from logpipe.query import Pipeline, Stage
from logpipe.stages.aggregate import AggregateStage
from logpipe.stages.where import WhereStage, parse_predicate
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
    group_by: Annotated[str | None, typer.Option("--group-by", help="Comma-separated field(s) to group by, e.g. 'host' or 'host,method'")] = None,
):
    """Query log records with a filter expression."""
    stages: list[Stage] = [WhereStage(parse_predicate(expr))]
    if window is not None:
        stages.append(WindowStage(WindowSpec(size_secs=parse_duration(window))))
    if group_by is not None:
        fields = [f.strip() for f in group_by.split(",")]
        stages.append(AggregateStage(fields))

    pipeline = Pipeline(stages)
    fh = sys.stdin if source == "-" else open(source)
    try:
        raw_records = (parse_log_record(line) for line in fh)
        valid_records = (r for r in raw_records if r is not None)
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
    finally:
        if fh is not sys.stdin:
            fh.close()


if __name__ == "__main__":
    app()
