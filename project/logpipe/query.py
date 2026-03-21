from __future__ import annotations

from typing import Any, Iterable, Protocol


class Stage(Protocol):
    def process(self, records: Iterable[Any]) -> Iterable[Any]: ...


class Pipeline:
    def __init__(self, stages: list[Stage]) -> None:
        self.stages = stages

    def run(self, source: Iterable[Any]) -> Iterable[Any]:
        stream: Iterable[Any] = source
        for stage in self.stages:
            stream = stage.process(stream)
        return stream
