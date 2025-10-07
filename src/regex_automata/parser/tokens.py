from dataclasses import dataclass


@dataclass
class Token:
    span: tuple[int, int]


@dataclass
class Character(Token):
    c: str


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
