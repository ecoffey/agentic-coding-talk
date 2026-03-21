import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def run(tmp_path):
    """Run `logpipe` as a subprocess. Returns (stdout, stderr, returncode)."""
    def _run(*args, stdin: str | None = None):
        result = subprocess.run(
            [sys.executable, "-m", "logpipe", *args],
            input=stdin,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        return result.stdout, result.stderr, result.returncode

    return _run


@pytest.fixture
def log_line():
    return '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.1" 200 1234 0.021'


@pytest.fixture
def log_file(tmp_path, log_line):
    f = tmp_path / "access.log"
    f.write_text(log_line + "\n")
    return f


@pytest.fixture
def make_log_line():
    """Return a factory for building valid log lines from explicit field values."""
    def _make(
        host: str = "127.0.0.1",
        user: str = "frank",
        timestamp: str = "10/Oct/2000:13:55:36 -0700",
        method: str = "GET",
        path: str = "/index.html",
        protocol: str = "HTTP/1.1",
        status: int = 200,
        bytes: int = 1234,
        response_time: float = 0.021,
    ) -> str:
        return (
            f'{host} - {user} [{timestamp}] '
            f'"{method} {path} {protocol}" '
            f'{status} {bytes} {response_time}'
        )
    return _make
