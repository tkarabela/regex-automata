from dataclasses import dataclass
from typing import Self


@dataclass
class Match:
    span: tuple[int, int]
    match: str

    @classmethod
    def from_span_and_text(cls, start: int, end: int, text: str) -> Self:
        return cls((start, end), text[start:end])

    def group(self) -> str:
        return self.match
