from dataclasses import dataclass
from typing import Iterator

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


@dataclass
class AstCharacter(AstNode):
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
class AstIteration(AstNode):
    u: AstNode

    def get_label(self) -> str:
        return "*"

    def iter_children(self) -> Iterator["AstNode"]:
        yield self.u


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
        return "<empty>"
