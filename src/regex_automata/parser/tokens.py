from dataclasses import dataclass
from typing import Self

from regex_automata.automata.rangeset import RangeSet


@dataclass
class Token:
    span: tuple[int, int]
    text: str

    @classmethod
    def from_span(cls: Self, s: str, span: tuple[int, int], **kwargs) -> Self:
        return cls(span, s[span[0]:span[1]], **kwargs)


@dataclass
class CharacterSet(Token):
    set: RangeSet


@dataclass
class Star(Token):
    pass


@dataclass
class LPar(Token):
    pass


@dataclass
class RPar(Token):
    pass


@dataclass
class Pipe(Token):
    pass
