import json
import sys
from dataclasses import asdict
from typing import Annotated

import typer

from logpipe.parser import parse_log_record
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
):
    """Query log records with a filter expression."""
    pipeline = Pipeline([WhereStage(parse_predicate(expr))])
    fh = sys.stdin if source == "-" else open(source)
    try:
        raw_records = (parse_log_record(line) for line in fh)
        valid_records = (r for r in raw_records if r is not None)
        for record in pipeline.run(valid_records):
            print(json.dumps(asdict(record)))
    finally:
        if fh is not sys.stdin:
            fh.close()


if __name__ == "__main__":
    app()
