import json
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def multi_log(tmp_path, make_log_line):
    """A log file with lines of varying status, method, path, response_time."""
    lines = [
        make_log_line(),                                                            # GET /index.html 200 0.021
        make_log_line(status=404, bytes=0, response_time=0.005),                   # GET /index.html 404
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
