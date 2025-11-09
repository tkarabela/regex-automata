from typing import Iterator, NoReturn

from .tokens import Token, LPar, RPar, Repetition, Pipe, CharacterSet, BoundaryAssertion, BoundaryAssertionSemantic
from ..automata.rangeset import RangeSet, WORD_RANGESET, NONWORD_RANGESET, DIGIT_RANGESET, NONDIGIT_RANGESET, \
    WHITESPACE_RANGESET, NONWHITESPACE_RANGESET
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

        def read_number(self) -> int:
            digits = []
            while c := self.tokenizer.peek():
                if c.isdigit():
                    digits.append(self.read())
                else:
                    break

            try:
                return int("".join(digits))
            except Exception as e:
                self.tokenizer.error(f"failed to read number ({e})")

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

    def normalize_case(self, s: str) -> str:
        if self.flags & PatternFlag.IGNORECASE:
            return s.lower()
        else:
            return s

    def read(self) -> str:
        self.pos += 1
        try:
            return self.text[self.pos]
        except IndexError:
            self.error("unexpected end of input")

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
                case "*" | "?" | "+" | "{":
                    yield self.read_Repetition(reader)
                case "|":
                    yield self.read_Pipe(reader)
                case ".":
                    yield self.read_CharacterSet(reader)
                case "^" | "$":
                    yield self.read_BoundaryAssertion(reader)
                case "\\":
                    match self.peek(k=2):
                        case None:
                            self.error("unfinished escape sequence")
                        case "A" | "Z" | "b" | "B":
                            yield self.read_BoundaryAssertion(reader)
                        case _:
                            yield self.read_CharacterSet(reader)
                case "." | "[" | _:
                    yield self.read_CharacterSet(reader)

    def read_LPar(self, reader: Reader) -> LPar:
        reader.read("(")
        return LPar(reader.span, reader.text)

    def read_RPar(self, reader: Reader) -> RPar:
        reader.read(")")
        return RPar(reader.span, reader.text)

    def read_Repetition(self, reader: Reader) -> Repetition:
        match reader.read():
            case "*":
                return Repetition(reader.span, reader.text, 0, None)
            case "?":
                return Repetition(reader.span, reader.text, 0, 1)
            case "+":
                return Repetition(reader.span, reader.text, 1, None)
            case "{":
                read_lower_limit = False
                c = self.peek()
                if c is None:
                    self.error("bad repetition definition")
                elif c == ",":
                    rmin = 0
                elif c.isdigit():
                    rmin = reader.read_number()
                    read_lower_limit = True
                else:
                    self.error("bad repetition definition")

                c = self.peek()
                if c is None:
                    self.error("bad repetition definition")
                elif c == ",":
                    reader.read(",")

                    c = self.peek()
                    if c == "}":
                        rmax = None
                    elif c is not None and c.isdigit():
                        rmax = reader.read_number()
                    else:
                        self.error("bad repetition definition")
                elif c == "}":
                    if not read_lower_limit:
                        self.error("bad repetition definition (braced definition missing both limits)")
                    rmax = rmin
                else:
                    self.error("bad repetition definition")

                reader.read("}")

                return Repetition(reader.span, reader.text, rmin, rmax)

            case _:
                self.error("bad repetition definition")

    def read_Pipe(self, reader: Reader) -> Pipe:
        reader.read("|")
        return Pipe(reader.span, reader.text)

    def read_CharacterSet(self, reader: Reader) -> CharacterSet:
        match self.peek():
            case "\\":
                reader.read("\\")
                match self.peek():
                    case None:
                        self.error("unfinished escape sequence")
                    case "w":
                        reader.read("w")
                        return CharacterSet(reader.span, reader.text, set=WORD_RANGESET)
                    case "W":
                        reader.read("W")
                        return CharacterSet(reader.span, reader.text, set=NONWORD_RANGESET)
                    case "d":
                        reader.read("d")
                        return CharacterSet(reader.span, reader.text, set=DIGIT_RANGESET)
                    case "D":
                        reader.read("D")
                        return CharacterSet(reader.span, reader.text, set=NONDIGIT_RANGESET)
                    case "s":
                        reader.read("s")
                        return CharacterSet(reader.span, reader.text, set=WHITESPACE_RANGESET)
                    case "S":
                        reader.read("S")
                        return CharacterSet(reader.span, reader.text, set=NONWHITESPACE_RANGESET)
                    case _:
                        c = reader.read()
                        return CharacterSet(reader.span, reader.text, set=RangeSet([ord(self.normalize_case(c))]))
            case ".":
                reader.read(".")
                if self.flags & PatternFlag.DOTALL:
                    return CharacterSet(reader.span, reader.text, set=RangeSet(complement=True))
                else:
                    return CharacterSet(reader.span, reader.text, set=RangeSet([ord("\n")], complement=True))
            case "[":
                return self._read_CharacterSet_brackets(reader)
            case _:
                c = reader.read()
                return CharacterSet(reader.span, reader.text, set=RangeSet([ord(self.normalize_case(c))]))

    def _read_CharacterSet_brackets(self, reader: Reader) -> CharacterSet:
        rs = RangeSet()
        complement = False
        reader.read("[")

        # special cases at start of inside of brackets
        if self.peek() == "^":
            complement = True
            reader.read("^")
        match c := self.peek():
            case "]" | "-":
                reader.read(c)
                rs |= {ord(c)}

        # TODO support escape sequences here
        running = True
        while running:
            match (self.peek(), self.peek(2), self.peek(3)):
                case (None, _, _):
                    self.error("unfinished character set")
                case ("]", _, _):
                    reader.read("]")
                    running = False
                case ("-", "]", _):
                    reader.read("-")
                    reader.read("]")
                    rs |= {ord("-")}
                    running = False
                case (c1, "-", c2):
                    match c2:
                        case "]":
                            reader.read(c1)
                            rs |= {ord(self.normalize_case(c1))}
                        case None:
                            self.error("unfinished character set")
                        case _:
                            reader.read(c1)
                            reader.read("-")
                            reader.read(c2)
                            start = ord(self.normalize_case(c1))
                            end = ord(self.normalize_case(c2))
                            if start > end:
                                self.error(f"malformed character set ({c1!r} > {c2!r})")
                            rs |= RangeSet(ranges=[(start, end+1)])
                case _:
                    c = reader.read()
                    rs |= {ord(self.normalize_case(c))}

        return CharacterSet(reader.span, reader.text, set=RangeSet(ranges=rs.ranges, complement=complement))

    def read_BoundaryAssertion(self, reader: Reader) -> BoundaryAssertion:
        match (self.peek(), self.peek(2)):
            case ("^", _):
                reader.read("^")
                return BoundaryAssertion(
                    reader.span,
                    reader.text,
                    BoundaryAssertionSemantic.LINE_START if self.flags & PatternFlag.MULTILINE else BoundaryAssertionSemantic.INPUT_START
                )
            case ("$", _):
                reader.read("$")
                return BoundaryAssertion(
                    reader.span,
                    reader.text,
                    BoundaryAssertionSemantic.LINE_END if self.flags & PatternFlag.MULTILINE else BoundaryAssertionSemantic.INPUT_END
                )
            case("\\", "A"):
                reader.read("\\")
                reader.read("A")
                return BoundaryAssertion(reader.span, reader.text, BoundaryAssertionSemantic.INPUT_START)
            case ("\\", "Z"):
                reader.read("\\")
                reader.read("Z")
                return BoundaryAssertion(reader.span, reader.text, BoundaryAssertionSemantic.INPUT_END)
            case ("\\", "b"):
                reader.read("\\")
                reader.read("b")
                return BoundaryAssertion(reader.span, reader.text, BoundaryAssertionSemantic.WORD_BOUNDARY)
            case ("\\", "B"):
                reader.read("\\")
                reader.read("B")
                return BoundaryAssertion(reader.span, reader.text, BoundaryAssertionSemantic.NONWORD_BOUNDARY)
            case _:
                self.error()
