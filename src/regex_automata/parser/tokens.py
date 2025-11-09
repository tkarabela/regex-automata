from dataclasses import dataclass
from enum import Enum

from regex_automata.automata.rangeset import RangeSet


@dataclass
class Token:
    span: tuple[int, int]
    text: str


@dataclass
class CharacterSet(Token):
    set: RangeSet


@dataclass
class Repetition(Token):
    min: int
    max: int | None


@dataclass
class LPar(Token):
    number: int
    non_capturing: bool = False
    symbolic_name: str | None = None


@dataclass
class RPar(Token):
    pass


@dataclass
class Pipe(Token):
    pass


class BoundaryAssertionSemantic(Enum):
    INPUT_START = "INPUT_START"
    INPUT_END = "INPUT_END"
    LINE_START = "LINE_START"
    LINE_END = "LINE_END"
    WORD_BOUNDARY = "WORD_BOUNDARY"
    NONWORD_BOUNDARY = "NONWORD_BOUNDARY"


@dataclass
class BoundaryAssertion(Token):
    semantic: BoundaryAssertionSemantic
