from dataclasses import dataclass


@dataclass
class AstNode:
    pass


@dataclass
class AstCharacter(AstNode):
    c: str


@dataclass
class AstConcatenation(AstNode):
    u: AstNode
    v: AstNode


@dataclass
class AstIteration(AstNode):
    u: AstNode


@dataclass
class AstUnion(AstNode):
    u: AstNode
    v: AstNode
