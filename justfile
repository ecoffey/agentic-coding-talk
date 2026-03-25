# logpipe live demos
# Run from repo root: just demo0 / demo1 / demo2 / demo3

# Demo 0 — raw log lines (the input to all other demos)
demo0:
    cat project/demo.log

# Demo 1 — WHERE: filter to only error responses
demo1:
    cd project && uv run python -m logpipe query "status >= 400" demo.log

# Demo 2 — WINDOW: bucket all requests into 1-minute tumbling windows
demo2:
    cd project && uv run python -m logpipe query "status >= 200" demo.log --window 1m

# Demo 3 — AGGREGATE: per-window error counts grouped by status code
demo3:
    cd project && uv run python -m logpipe query "status >= 200" demo.log --window 1m --group-by status
