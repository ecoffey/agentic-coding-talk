import json

import pytest


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

TS_BUCKET_2 = "10/Oct/2000:14:01:36 -0700"
BUCKET_1_START = 971211300
BUCKET_1_END   = 971211600
BUCKET_2_START = 971211600
BUCKET_2_END   = 971211900


@pytest.fixture
def two_host_log(tmp_path, make_log_line):
    """Three records: 2 from host-a, 1 from host-b."""
    lines = [
        make_log_line(host="host-a", status=200, bytes=1000, response_time=0.1),
        make_log_line(host="host-a", status=404, bytes=500,  response_time=0.2),
        make_log_line(host="host-b", status=200, bytes=800,  response_time=0.05),
    ]
    f = tmp_path / "two_host.log"
    f.write_text("\n".join(lines) + "\n")
    return f


@pytest.fixture
def window_two_host_log(tmp_path, make_log_line):
    """
    Two buckets, two hosts each:
      bucket1: host-a 200, host-b 404
      bucket2: host-a 500
    """
    lines = [
        make_log_line(host="host-a", status=200, bytes=1000, response_time=0.1),
        make_log_line(host="host-b", status=404, bytes=500,  response_time=0.2),
        make_log_line(host="host-a", status=500, bytes=200,  response_time=0.5,
                      timestamp=TS_BUCKET_2),
    ]
    f = tmp_path / "window_two_host.log"
    f.write_text("\n".join(lines) + "\n")
    return f


# ---------------------------------------------------------------------------
# Basic GROUP BY tests (no window)
# ---------------------------------------------------------------------------

def test_group_by_produces_one_row_per_group(run, two_host_log):
    stdout, _, code = run("query", "status >= 200", "--group-by", "host",
                          str(two_host_log))
    assert code == 0
    rows = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    hosts = {r["host"] for r in rows}
    assert hosts == {"host-a", "host-b"}
    assert len(rows) == 2


def test_group_by_count(run, two_host_log):
    stdout, _, code = run("query", "status >= 200", "--group-by", "host",
                          str(two_host_log))
    assert code == 0
    rows = {r["host"]: r for r in
            [json.loads(l) for l in stdout.splitlines() if l.strip()]}
    assert rows["host-a"]["count"] == 2
    assert rows["host-b"]["count"] == 1


def test_group_by_numeric_stats(run, two_host_log):
    stdout, _, code = run("query", "status >= 200", "--group-by", "host",
                          str(two_host_log))
    assert code == 0
    rows = {r["host"]: r for r in
            [json.loads(l) for l in stdout.splitlines() if l.strip()]}
    a = rows["host-a"]
    assert a["bytes_sum"] == 1500
    assert a["bytes_min"] == 500
    assert a["bytes_max"] == 1000
    assert abs(a["response_time_avg"] - 0.15) < 1e-9


def test_group_by_no_match(run, two_host_log):
    stdout, _, code = run("query", "status = 999", "--group-by", "host",
                          str(two_host_log))
    assert code == 0
    assert stdout.strip() == ""


def test_group_by_multi_field(run, tmp_path, make_log_line):
    lines = [
        make_log_line(host="h1", method="GET"),
        make_log_line(host="h1", method="POST"),
        make_log_line(host="h1", method="GET"),
    ]
    f = tmp_path / "multi.log"
    f.write_text("\n".join(lines) + "\n")
    stdout, _, code = run("query", "status >= 200", "--group-by", "host,method",
                          str(f))
    assert code == 0
    rows = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(rows) == 2
    counts = {(r["host"], r["method"]): r["count"] for r in rows}
    assert counts[("h1", "GET")] == 2
    assert counts[("h1", "POST")] == 1


# ---------------------------------------------------------------------------
# GROUP BY + WINDOW
# ---------------------------------------------------------------------------

def test_group_by_with_window(run, window_two_host_log):
    stdout, _, code = run("query", "status >= 200",
                          "--window", "5m",
                          "--group-by", "host",
                          str(window_two_host_log))
    assert code == 0
    rows = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    # bucket1: host-a(1), host-b(1) → 2 rows; bucket2: host-a(1) → 1 row
    assert len(rows) == 3


def test_group_by_with_window_metadata(run, window_two_host_log):
    stdout, _, code = run("query", "status >= 200",
                          "--window", "5m",
                          "--group-by", "host",
                          str(window_two_host_log))
    assert code == 0
    rows = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    for row in rows:
        assert "window_start" in row
        assert "window_end" in row
    b1_rows = [r for r in rows if r["window_start"] == BUCKET_1_START]
    b2_rows = [r for r in rows if r["window_start"] == BUCKET_2_START]
    assert len(b1_rows) == 2
    assert len(b2_rows) == 1
