from dataclasses import dataclass

from regex_automata.automata.rangeset import RangeSet


@dataclass
class Token:
    span: tuple[int, int]
    text: str


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
