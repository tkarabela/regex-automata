import functools
from typing import Type, TypeVar, NoReturn, ParamSpec, Callable

from .tokens import Token, LPar, RPar, Star, Pipe, Character
from .ast import AstNode, AstUnion, AstIteration, AstCharacter, AstConcatenation
from ..errors import ParserError


T = TypeVar("T")
P = ParamSpec("P")
TToken = TypeVar("TToken", bound=Token)


def rule(f: Callable[P, T]) -> Callable[P, T]:
    @functools.wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        print(f"using rule {f.__name__:3} :", str(f.__doc__).strip())
        return f(*args, **kwargs)
    return wrapper


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = list(tokens)
        self.pos = -1
        self.string_pos = -1

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
            print("reading", t)
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

    @rule
    def p1(self) -> AstNode:
        """
        E  -> F E'
        """
        # F
        match self.peek():
            case LPar():
                F = self.p4()
            case Character():
                F = self.p4()
            case _:
                self.error()

        # E'
        Eprime: AstNode | None
        match self.peek():
            case Pipe():
                Eprime = self.p2()
            case RPar():
                Eprime = self.p3()
            case None:
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
            case LPar():
                E = self.p1()
            case Character():
                E = self.p1()
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
            case LPar():
                G = self.p7()
            case Character():
                G = self.p7()
            case _:
                self.error()

        # F'
        Fprime: AstNode | None
        match self.peek():
            case LPar():
                Fprime = self.p5()
            case Character():
                Fprime = self.p5()
            case Pipe():
                Fprime = self.p6()
            case RPar():
                Fprime = self.p6()
            case None:
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
            case LPar():
                G = self.p7()
            case Character():
                G = self.p7()
            case _:
                self.error()

        # F'
        Fprime: AstNode | None
        match self.peek():
            case LPar():
                Fprime = self.p5()
            case Character():
                Fprime = self.p5()
            case Pipe():
                Fprime = self.p6()
            case RPar():
                Fprime = self.p6()
            case None:
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
            case Character():
                H = self.p11()
            case _:
                self.error()

        # G'
        match self.peek():
            case LPar():
                Gprime = self.p9(H)
            case Character():
                Gprime = self.p9(H)
            case Pipe():
                Gprime = self.p9(H)
            case Star():
                Gprime = self.p8(H)
            case RPar():
                Gprime = self.p9(H)
            case None:
                Gprime = self.p9(H)
            case _:
                self.error()

        return Gprime

    @rule
    def p8(self, Gprime: AstNode) -> AstNode:
        """
        G' -> star
        """
        _ = self.read(Star)
        return AstIteration(Gprime)

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
        _ = self.read(LPar)

        # E
        match self.peek():
            case LPar():
                E = self.p1()
            case Character():
                E = self.p1()
            case _:
                self.error()

        # rpar
        _ = self.read(RPar)

        return E

    @rule
    def p11(self) -> AstNode:
        """
        H  -> a
        """
        a = self.read(Character)
        return AstCharacter(a.c)
