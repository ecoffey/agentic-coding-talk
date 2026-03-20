import re
from dataclasses import dataclass
from datetime import datetime

LOG_PATTERN = re.compile(
    r'(?P<host>\S+) \S+ (?P<user>\S+) \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" (?P<status>\d{3}) (?P<bytes>\d+|-) '
    r'(?P<response_time>\d+(?:\.\d+)?)'
)

TIMESTAMP_FORMAT = "%d/%b/%Y:%H:%M:%S %z"


@dataclass
class LogRecord:
    host: str
    user: str
    ts: int
    method: str
    path: str
    status: int
    bytes: int | None
    response_time: float


def parse_line(line: str) -> LogRecord | None:
    m = LOG_PATTERN.match(line.strip())
    if not m:
        return None
    d = m.groupdict()
    try:
        ts = int(datetime.strptime(d["timestamp"], TIMESTAMP_FORMAT).timestamp())
    except ValueError:
        return None
    return LogRecord(
        host=d["host"],
        user=d["user"],
        ts=ts,
        method=d["method"],
        path=d["path"],
        status=int(d["status"]),
        bytes=int(d["bytes"]) if d["bytes"] != "-" else None,
        response_time=float(d["response_time"]),
    )
