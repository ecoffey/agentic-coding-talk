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
