from copy import deepcopy
from dataclasses import dataclass
from typing import Iterator, Self

from regex_automata.automata.nfa import LabeledRangeSet


@dataclass
class AstNode:
    def get_label(self) -> str:
        raise NotImplementedError

    def iter_children(self) -> Iterator["AstNode"]:
        yield from ()

    def iter_descendants(self) -> Iterator["AstNode"]:
        yield self
        for u in self.iter_children():
            yield from u.iter_descendants()

    def copy(self) -> Self:
        return deepcopy(self)


@dataclass
class AstCharacterSet(AstNode):
    lrs: LabeledRangeSet

    def get_label(self) -> str:
        return self.lrs.label


@dataclass
class AstConcatenation(AstNode):
    u: AstNode
    v: AstNode

    def get_label(self) -> str:
        return "·"

    def iter_children(self) -> Iterator["AstNode"]:
        yield from (self.u, self.v)


@dataclass
class AstRepetition(AstNode):
    u: AstNode
    min: int
    max: int | None

    def get_label(self) -> str:
        match self.min, self.max:
            case 0, 1:
                return "?"
            case 0, None:
                return "*"
            case 1, None:
                return "+"
            case _, None:
                return f"{{{self.min},}}"
            case _:
                return f"{{{self.min},{self.max}}}"

    def iter_children(self) -> Iterator["AstNode"]:
        yield self.u


@dataclass(init=False)
class AstIteration(AstRepetition):
    """Kleene star"""
    def __init__(self, u: AstNode) -> None:
        super().__init__(u=u, min=0, max=None)


@dataclass
class AstUnion(AstNode):
    u: AstNode
    v: AstNode

    def get_label(self) -> str:
        return "|"

    def iter_children(self) -> Iterator["AstNode"]:
        yield from (self.u, self.v)


@dataclass
class AstEmpty(AstNode):
    def get_label(self) -> str:
        return "ε"
