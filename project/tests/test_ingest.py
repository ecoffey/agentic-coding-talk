import json


def test_single_valid_line(run, log_file):
    stdout, _, code = run("ingest", str(log_file))
    assert code == 0
    lines = [l for l in stdout.splitlines() if l.strip()]
    assert len(lines) == 1


def test_all_fields_present(run, log_file):
    stdout, _, _ = run("ingest", str(log_file))
    record = json.loads(stdout.strip())
    assert set(record.keys()) == {"host", "user", "ts", "method", "path", "status", "bytes", "response_time"}


def test_timestamp_is_epoch(run, log_file):
    stdout, _, _ = run("ingest", str(log_file))
    record = json.loads(stdout.strip())
    assert isinstance(record["ts"], int)
    assert record["ts"] == 971211336


def test_stdin_input(run, log_line):
    stdout, _, code = run("ingest", "-", stdin=log_line + "\n")
    assert code == 0
    record = json.loads(stdout.strip())
    assert record["path"] == "/index.html"


def test_malformed_line_skipped(run, tmp_path):
    bad = tmp_path / "bad.log"
    bad.write_text("this is not a log line\n")
    stdout, _, code = run("ingest", str(bad))
    assert code == 0
    assert stdout.strip() == ""


def test_mixed_valid_invalid(run, tmp_path, log_line):
    f = tmp_path / "mixed.log"
    f.write_text(
        log_line + "\n"
        "not a log line\n"
        + log_line.replace("/index.html", "/about.html") + "\n"
    )
    stdout, _, code = run("ingest", str(f))
    assert code == 0
    lines = [l for l in stdout.splitlines() if l.strip()]
    assert len(lines) == 2
    paths = [json.loads(l)["path"] for l in lines]
    assert "/index.html" in paths
    assert "/about.html" in paths
