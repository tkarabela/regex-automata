from typing import Iterator

from .tokens import Token, LPar, RPar, Star, Pipe, CharacterSet
from ..automata.rangeset import RangeSet
from ..errors import TokenizerError
from ..regex.flags import PatternFlag


class Tokenizer:
    def __init__(self, s: str, flags: PatternFlag = PatternFlag.NOFLAG) -> None:
        self.s = s
        self.s_effective = s.lower() if flags & PatternFlag.IGNORECASE else s
        self.flags = flags

    def get_tokens(self) -> Iterator[Token]:
        i = 0
        while i < len(self.s):
            c = self.s[i]

            span = (i, i + 1)
            match c:
                case "(":
                    yield LPar.from_span(self.s, span)
                case ")":
                    yield RPar.from_span(self.s, span)
                case "*":
                    yield Star.from_span(self.s, span)
                case "|":
                    yield Pipe.from_span(self.s, span)
                case ".":
                    if self.flags & PatternFlag.DOTALL:
                        yield CharacterSet.from_span(self.s, span, set=RangeSet(complement=True))
                    else:
                        yield CharacterSet.from_span(self.s, span, set=RangeSet([ord("\n")], complement=True))
                case "^" | "$" | "+" | "?" | "{" | "[":
                    raise TokenizerError(f"special character {c!r} is not implemented", i)  # TODO
                case "\\":
                    span = (i, i + 2)
                    try:
                        yield CharacterSet.from_span(self.s, span, set=RangeSet([ord(self.s_effective[i+1])]))
                    except IndexError:
                        raise TokenizerError("unfinished escape sequence", i)
                case _:
                    yield CharacterSet.from_span(self.s, span, set=RangeSet([ord(self.s_effective[i])]))
            i = span[1]
