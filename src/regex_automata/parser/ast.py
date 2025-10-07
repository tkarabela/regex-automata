from dataclasses import dataclass
from typing import Iterator


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
    c: str

    def get_label(self) -> str:
        return self.c


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
