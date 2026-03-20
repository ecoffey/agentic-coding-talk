# logpipe

A log analytics CLI built as a demo for ATLS 4214.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
cd project
uv sync
```

## Usage

### Ingest logs

Parse log lines and echo them as JSON:

```bash
uv run logpipe access.log
uv run logpipe -          # read from stdin
```

Output is one JSON object per valid line:

```json
{"host": "127.0.0.1", "user": "-", "ts": 971211336, "method": "GET", "path": "/index.html", "status": 200, "bytes": 1234, "response_time": 0.021}
```

Malformed lines are silently skipped.

## Run tests

```bash
uv run pytest
```

## Log format

Expects Extended Combined Log Format — standard Apache/nginx access logs with an
appended `response_time` field (seconds):

```
127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.1" 200 1234 0.021
```
