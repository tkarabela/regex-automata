import functools
from typing import Type, TypeVar, NoReturn, ParamSpec, Callable

from .tokens import Token, LPar, RPar, Repetition, Pipe, CharacterSet, BoundaryAssertion
from .ast import AstNode, AstUnion, AstRepetition, AstCharacterSet, AstConcatenation, AstEmpty, AstBoundaryAssertion, \
    AstGroup
from ..common import root_logger
from ..errors import ParserError

logger = root_logger.getChild("parser")

T = TypeVar("T")
P = ParamSpec("P")
TToken = TypeVar("TToken", bound=Token)


def rule(f: Callable[P, T]) -> Callable[P, T]:
    @functools.wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        logger.info(f"using rule {f.__name__:3} : {str(f.__doc__).strip()}")
        return f(*args, **kwargs)
    return wrapper


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = list(tokens)
        self.pos = -1
        self.string_pos = -1
        self.group_name_to_group_number: dict[str, int] = {}

    def read(self, cls: Type[TToken]) -> TToken:
        self.pos += 1
        try:
            t = self.tokens[self.pos]
        except IndexError:
            self.error(f"expected {cls.__name__}, got end of input")
        self.string_pos = t.span[-1] - 1
        if not isinstance(t, cls):
            self.error(f"expected {cls.__name__}, read {t.__class__.__name__}")
        else:
            logger.info("reading %r", t)
            return t

    def peek(self) -> Token | None:
        i = self.pos + 1
        return self.tokens[i] if i < len(self.tokens) else None

    def error(self, description: str | None = None) -> NoReturn:
        msg = f"error at position {self.string_pos}"
        if description:
            msg += f": {description}"
        raise ParserError(msg, self.string_pos)

    def parse(self) -> AstNode:
        root = self.p1()
        if self.peek() is not None:
            self.error("unread input remaining (expected end of input)")
        return root

    def make_group(self, u: AstNode, number: int, name: str | None = None) -> AstGroup:
        if name is not None:
            self.group_name_to_group_number[name] = number
        return AstGroup(number, u, name)

    @rule
    def p1(self) -> AstNode:
        """
        E  -> F E'
        """
        # F
        match self.peek():
            case LPar() | CharacterSet() | BoundaryAssertion():
                F = self.p4()
            case RPar() | None:
                F = self.p13()
            case _:
                self.error()

        # E'
        Eprime: AstNode | None
        match self.peek():
            case Pipe():
                Eprime = self.p2()
            case RPar() | None:
                Eprime = self.p3()
            case _:
                self.error()

        if Eprime is None:
            return F
        else:
            return AstUnion(F, Eprime)

    @rule
    def p2(self) -> AstNode:
        """
        E' -> pipe E
        """
        # pipe
        _ = self.read(Pipe)

        # E
        match self.peek():
            case LPar() | CharacterSet() | BoundaryAssertion():
                E = self.p1()
            case RPar() | None:
                E = self.p12()
            case _:
                self.error()

        return E

    @rule
    def p3(self) -> None:
        """
        E' -> ε
        """
        return None

    @rule
    def p4(self) -> AstNode:
        """
        F  -> G F'
        """
        # G
        match self.peek():
            case LPar() | CharacterSet() | BoundaryAssertion():
                G = self.p7()
            case _:
                self.error()

        # F'
        Fprime: AstNode | None
        match self.peek():
            case LPar() | CharacterSet() | BoundaryAssertion():
                Fprime = self.p5()
            case Pipe() | RPar() | None:
                Fprime = self.p6()
            case _:
                self.error()

        if Fprime is None:
            return G
        else:
            return AstConcatenation(G, Fprime)

    @rule
    def p5(self) -> AstNode:
        """
        F' -> G F'
        """
        # G
        match self.peek():
            case LPar() | CharacterSet() | BoundaryAssertion():
                G = self.p7()
            case _:
                self.error()

        # F'
        Fprime: AstNode | None
        match self.peek():
            case LPar() | CharacterSet() | BoundaryAssertion():
                Fprime = self.p5()
            case Pipe() | RPar() | None:
                Fprime = self.p6()
            case _:
                self.error()

        if Fprime is None:
            return G
        else:
            return AstConcatenation(G, Fprime)

    @rule
    def p6(self) -> None:
        """
        F' -> ε
        """
        return None

    @rule
    def p7(self) -> AstNode:
        """
        G  -> H G'
        """
        # H
        match self.peek():
            case LPar():
                H = self.p10()
            case CharacterSet():
                H = self.p11()
            case BoundaryAssertion():
                H = self.p14()
            case _:
                self.error()

        # G'
        match self.peek():
            case Repetition():
                Gprime = self.p8(H)
            case LPar() | CharacterSet() | BoundaryAssertion() | Pipe() | RPar() | None:
                Gprime = self.p9(H)
            case _:
                self.error()

        return Gprime

    @rule
    def p8(self, Gprime: AstNode) -> AstNode:
        """
        G' -> star
        """
        repetition = self.read(Repetition)
        return AstRepetition(Gprime, repetition.min, repetition.max)

    @rule
    def p9(self, Gprime: AstNode) -> AstNode:
        """
        G' -> ε
        """
        return Gprime

    @rule
    def p10(self) -> AstNode:
        """
        H  -> lpar E rpar
        """
        # lpar
        lpar = self.read(LPar)

        # E
        match self.peek():
            case LPar() | CharacterSet() | BoundaryAssertion():
                E = self.p1()
            case RPar():
                E = self.p12()
            case _:
                self.error()

        # rpar
        _ = self.read(RPar)

        if lpar.non_capturing:
            return E
        else:
            return self.make_group(E, lpar.number, lpar.symbolic_name)

    @rule
    def p11(self) -> AstNode:
        """
        H  -> a
        """
        a = self.read(CharacterSet)
        return AstCharacterSet(
            rs=a.set,
            label=a.text
        )

    @rule
    def p12(self) -> AstNode:
        """
        E  -> ε
        """
        return AstEmpty()

    @rule
    def p13(self) -> AstNode:
        """
        F  -> ε
        """
        return AstEmpty()

    @rule
    def p14(self) -> AstNode:
        """
        H  -> boundary_assertion
        """
        boundary = self.read(BoundaryAssertion)
        return AstBoundaryAssertion(boundary.semantic)
