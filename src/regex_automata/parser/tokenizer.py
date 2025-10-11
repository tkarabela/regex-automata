from typing import Iterator, NoReturn

from .tokens import Token, LPar, RPar, Star, Pipe, CharacterSet
from ..automata.rangeset import RangeSet
from ..errors import TokenizerError
from ..regex.flags import PatternFlag


class Tokenizer:
    class Reader:
        def __init__(self, tokenizer: "Tokenizer") -> None:
            self.tokenizer = tokenizer
            self.start = tokenizer.pos + 1
            self.end = self.start

        def read(self, expect: str | None = None) -> str:
            c = self.tokenizer.read()
            if expect is not None and expect != c:
                self.tokenizer.error(f"expected to read {expect!r}, got {c!r}")
            self.end = self.tokenizer.pos + 1
            return c

        @property
        def span(self) -> tuple[int, int]:
            return self.start, self.end

        @property
        def text(self) -> str:
            return self.tokenizer.text[self.start:self.end]

    def __init__(self, text: str, flags: PatternFlag = PatternFlag.NOFLAG) -> None:
        self.text = text
        self.flags = flags
        self.pos = -1

    def read(self) -> str:
        self.pos += 1
        try:
            return self.text[self.pos]
        except IndexError:
            self.error(f"unexpected end of input")

    def peek(self, k: int = 1) -> str | None:
        i = self.pos + k
        return self.text[i] if i < len(self.text) else None

    def error(self, description: str | None = None) -> NoReturn:
        msg = f"error at position {self.pos}"
        if description:
            msg += f": {description}"
        raise TokenizerError(msg, self.pos)

    def get_tokens(self) -> Iterator[Token]:
        while c := self.peek():
            reader = self.Reader(self)

            match c:
                case "(":
                    yield self.read_LPar(reader)
                case ")":
                    yield self.read_RPar(reader)
                case "*":
                    yield self.read_Star(reader)
                case "|":
                    yield self.read_Pipe(reader)
                case ".":
                    yield self.read_CharacterSet(reader)
                case "^" | "$" | "+" | "?" | "{" | "[":
                    self.error(f"special character {c!r} is not implemented")  # TODO
                case "\\":
                    match self.peek(k=2):
                        case None:
                            self.error("unfinished escape sequence")
                        case _:
                            yield self.read_CharacterSet(reader)
                case _:
                    yield self.read_CharacterSet(reader)

    def read_LPar(self, reader: Reader) -> Token:
        reader.read("(")
        return LPar(reader.span, reader.text)

    def read_RPar(self, reader: Reader) -> Token:
        reader.read(")")
        return RPar(reader.span, reader.text)

    def read_Star(self, reader: Reader) -> Token:
        reader.read("*")
        return Star(reader.span, reader.text)

    def read_Pipe(self, reader: Reader) -> Token:
        reader.read("|")
        return Pipe(reader.span, reader.text)

    def read_CharacterSet(self, reader: Reader) -> Token:
        match c := self.peek():
            case "\\":
                reader.read("\\")
                c = self.peek()
                if c is None:
                    self.error("unfinished escape sequence")
                else:
                    reader.read()
                    if self.flags & PatternFlag.IGNORECASE:
                        c = c.lower()
                    return CharacterSet(reader.span, reader.text, set=RangeSet([ord(c)]))
            case ".":
                reader.read(".")
                if self.flags & PatternFlag.DOTALL:
                    return CharacterSet(reader.span, reader.text, set=RangeSet(complement=True))
                else:
                    return CharacterSet(reader.span, reader.text, set=RangeSet([ord("\n")], complement=True))
            case _:
                reader.read()
                if self.flags & PatternFlag.IGNORECASE:
                    c = c.lower()
                return CharacterSet(reader.span, reader.text, set=RangeSet([ord(c)]))
