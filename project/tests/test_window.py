import json
import pytest

# Bucket boundaries for 5-minute (300s) windows
# Default make_log_line timestamp "10/Oct/2000:13:55:36 -0700" → epoch 971211336
BUCKET_1_START = 971211300
BUCKET_1_END = 971211600

# "10/Oct/2000:14:01:36 -0700" → epoch 971211696
BUCKET_2_START = 971211600
BUCKET_2_END = 971211900
TS_BUCKET_2 = "10/Oct/2000:14:01:36 -0700"


@pytest.fixture
def window_log(tmp_path, make_log_line):
    """Log file with records spread across two 5-minute windows."""
    lines = [
        make_log_line(status=200),                              # bucket 1
        make_log_line(status=404),                              # bucket 1
        make_log_line(timestamp=TS_BUCKET_2, status=500),       # bucket 2
    ]
    f = tmp_path / "window.log"
    f.write_text("\n".join(lines) + "\n")
    return f


def test_window_no_match(run, window_log):
    stdout, _, code = run("query", "status = 999", "--window", "5m", str(window_log))
    assert code == 0
    assert stdout.strip() == ""


def test_window_single_bucket(run, tmp_path, make_log_line):
    """All records land in the same window → 1 bucket emitted."""
    lines = [make_log_line(status=200), make_log_line(status=404)]
    f = tmp_path / "single.log"
    f.write_text("\n".join(lines) + "\n")

    stdout, _, code = run("query", "status >= 200", "--window", "5m", str(f))
    assert code == 0
    buckets = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(buckets) == 1
    assert buckets[0]["window_start"] == BUCKET_1_START
    assert buckets[0]["window_end"] == BUCKET_1_END
    assert buckets[0]["count"] == 2
    assert len(buckets[0]["records"]) == 2


def test_window_two_buckets(run, window_log):
    """Records spanning two windows → 2 buckets in chronological order."""
    stdout, _, code = run("query", "status >= 200", "--window", "5m", str(window_log))
    assert code == 0
    buckets = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(buckets) == 2

    assert buckets[0]["window_start"] == BUCKET_1_START
    assert buckets[0]["window_end"] == BUCKET_1_END
    assert buckets[0]["count"] == 2

    assert buckets[1]["window_start"] == BUCKET_2_START
    assert buckets[1]["window_end"] == BUCKET_2_END
    assert buckets[1]["count"] == 1


def test_window_with_where_filter(run, window_log):
    """WHERE runs before WINDOW — only matching records appear in buckets."""
    # window_log has: 200 (bucket1), 404 (bucket1), 500 (bucket2)
    # filter status >= 400 → 404 (bucket1) and 500 (bucket2) survive
    stdout, _, code = run("query", "status >= 400", "--window", "5m", str(window_log))
    assert code == 0
    buckets = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(buckets) == 2
    assert buckets[0]["count"] == 1
    assert buckets[0]["records"][0]["status"] == 404
    assert buckets[1]["count"] == 1
    assert buckets[1]["records"][0]["status"] == 500


def test_window_stdin(run, make_log_line):
    """Window works when reading from stdin."""
    stdin = make_log_line(status=200) + "\n" + make_log_line(status=404) + "\n"
    stdout, _, code = run("query", "status >= 200", "--window", "5m", "-", stdin=stdin)
    assert code == 0
    buckets = [json.loads(l) for l in stdout.splitlines() if l.strip()]
    assert len(buckets) == 1
    assert buckets[0]["count"] == 2


def test_window_invalid_duration(run, tmp_path, make_log_line):
    """Bad --window value → non-zero exit."""
    f = tmp_path / "x.log"
    f.write_text(make_log_line() + "\n")
    _, _, code = run("query", "status >= 200", "--window", "5minutes", str(f))
    assert code != 0
